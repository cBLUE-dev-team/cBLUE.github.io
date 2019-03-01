import logging
logging.basicConfig(format='%(asctime)s:%(message)s', level=logging.INFO)
from Merge import Merge
from sympy import *
import numpy as np
import numexpr as ne

"""
This class provides the functionality to calculate the aerial
portion of the total propagated uncertainty (TPU).

Two key modules that are used throughout are sympy and numexpr.  
The module sympy ....  The module numexpr....  
        # assign variables because numexpr variables don't handle indexing

        for example...
         x_las = self.x_las
         x_ = ne.evaluate("x_las - x_sbet")
"""


class SensorModel:

    def __init__(self, sensor):
        self.sensor = sensor
        self.R, self.fR = self.set_rotation_matrix_airplane() 
        self.M = self.set_rotation_matrix_scanning_sensor()
        self.obs_eq = self.define_obseration_equation()

    @staticmethod
    def set_rotation_matrix_airplane():
        """define rotation matrix for airplane

        This method first generates the airplane rotation matrix, R, using
        symbolic calculations.  The symbolic components of the matrix R are
        then "functionized", or "lambdified", for faster processing (because
        symbolic calculations are relatively slow).  The components of R are
        functionized separately from the general observation equation, which
        includes R, M (the sensor rotation matrix), and polynomial-surface-
        correction terms, because R is later used to estimate parameters
        describing the assumed scan pattern, which is an approximation of the
        manufacturer's proprietary scan pattern.

        :return: Matrix
        :return: List[lambdify functions]
        """
        r, p, h = symbols('r p h')
        R1 = Matrix([[1, 0, 0],
                     [0, cos(r), -sin(r)],
                     [0, sin(r), cos(r)]])

        R2 = Matrix([[cos(p), 0, sin(p)],
                     [0, 1, 0],
                     [-sin(p), 0, cos(p)]])

        R3 = Matrix([[cos(h), -sin(h), 0],
                     [sin(h), cos(h), 0],
                     [0, 0, 1]])

        R = R3 * R2 * R1
        logging.info(R)

        # "functionize" the necessary R components for a, b, and w estimation
        # (http://docs.sympy.org/latest/modules/utilities/lambdify.html)
        r00 = lambdify((h, p), R[0], 'numexpr')
        r01 = lambdify((r, p, h), R[1], 'numexpr')
        r10 = lambdify((h, p), R[3], 'numexpr')
        r11 = lambdify((r, p, h), R[4], 'numexpr')
        r20 = lambdify(p, R[6], 'numexpr')
        r21 = lambdify((r, p), R[7], 'numexpr')
        fR = [r00, r01, None,
              r10, r11, None,
              r20, r21, None]
        return R, fR

    @staticmethod
    def set_rotation_matrix_scanning_sensor():
        """define the lidar sensor rotation matrix

        This method generates the rotation matrix associated with the
        scanning sensor.  The variables a, b, and w describe the assumed
        scan pattern, which is an approximation of the manufacturer's
        proprietary scan pattern.

        a: the rotation in the YZ plane
        b: the rotation in the XZ plane
        w: ?

        :return Matrix M: the scanning sensor rotation matrix
        """
        a, b, w = symbols('a b w')
        M1 = Matrix([[1, 0, 0],
                     [0, cos(a), -sin(a)],
                     [0, sin(a), cos(a)]])

        M2 = Matrix([[cos(b), 0, sin(b)],
                     [0, 1, 0],
                     [-sin(b), 0, cos(b)]])

        M3 = Matrix([[cos(w), -sin(w), 0],
                     [sin(w), cos(w), 0],
                     [0, 0, 1]])

        M = M3 * M2 * M1
        logging.info('sensor rotation matrix: {}'.format(M))
        return M

    def define_obseration_equation(self):
        """define the lidar geolocation observation equation

        The lidar geolocation equation used by cBLUE is shown below:

        TODO: add latex

        :return: (sympy object, sympy object, sympy object, function)
        """

        # create variables for symbolic computations
        a, b, w, r, p, h, x, y, z, rho, p00, p10, p01, p20, p11, p02, p21, p12, p03 \
            = symbols('a b w r p h x y z rho p00 p10 p01 p20 p11 p02 p21 p12 p03')

        # define observation equations
        # [00, 01, 02      matrix       [0 1 2
        #  10, 11, 12   ---indices-->    3 4 5
        #  20, 21, 22]                   6 7 8]
        F1 = x - rho * (self.R[0] * self.M[2] + self.R[1] * self.M[5] + self.R[2] * self.M[8])
        F2 = y - rho * (self.R[3] * self.M[2] + self.R[4] * self.M[5] + self.R[5] * self.M[8])
        F3 = z - rho * (self.R[6] * self.M[2] + self.R[7] * self.M[5] + self.R[8] * self.M[8])

        # converting symbolic to function (for faster computations)
        fF1 = lambdify((a, b, h, p, r, rho, w, x), F1, 'numexpr')
        fF2 = lambdify((a, b, h, p, r, rho, w, y), F2, 'numexpr')
        fF3 = lambdify((a, b, p, r, rho, w, z), F3, 'numexpr')
        fF_orig = [fF1, fF2, fF3]

        # least squares adjustment mimics the Matlab "fit (poly23)" function
        polysurfcorr = p00 + \
                       p10 * a + \
                       p01 * b + \
                       p20 * a ** 2 + \
                       p11 * a * b + \
                       p02 * b ** 2 + \
                       p21 * a ** 2 * b + \
                       p12 * a * b ** 2 + \
                       p03 * b ** 3

        # Redefine obs eqs by adding polynomial surface fitting eq
        F1 += polysurfcorr
        F2 += polysurfcorr
        F3 += polysurfcorr
        return (F1, F2, F3, fF_orig, )

    def estimate_rho_a_b(self, data):
        """calculates estimates for rho, alpha, and beta

        This method calculates the estimated values for rho, alpha, and beta, which
        are the lidar range, angle in the YZ plane, and angle in the XZ plane,
        respectively (see the following image).

        .. image:: ../images/rho_alpha_beta.png

        Alpha and beta are used to model the scan pattern, as a substitute for the
        actual, unknown, proprietary scan pattern model implemented by the
        manufacturer.  Polynomial-surface error modeling is used to account for the
        positional differences resulting from the difference between the cBLUE scan
        model and the manufacturer scan model.

        :return: (list[], list[], list[], list[])
        """

        x_las = self.x_las  # data.x_las
        y_las = self.y_las
        z_las = self.z_las
        x_sbet = self.x_sbet
        y_sbet = self.y_sbet
        z_sbet = self.z_sbet

        dx = ne.evaluate("x_las - x_sbet")
        dy = ne.evaluate("y_las - y_sbet")
        dz = ne.evaluate("z_las - z_sbet")

        fR0 = self.fR[0](self.h0, self.p0)
        fR3 = self.fR[3](self.h0, self.p0)
        fR6 = self.fR[6](self.p0)
        fR1 = self.fR[1](self.r0, self.p0, self.h0)
        fR4 = self.fR[4](self.r0, self.p0, self.h0)
        fR7 = self.fR[7](self.r0, self.p0)

        rho_est = ne.evaluate("sqrt(dx**2 + dy**2 + dz**2)")
        b_est = ne.evaluate("arcsin(((fR0 * dx) + (fR3 * dy) + (fR6 * dz)) / (-rho_est))")
        a_est = ne.evaluate("arcsin(((fR1 * dx) + (fR4 * dy) + (fR7 * dz)) / (rho_est * cos(b_est)))")
        w_est = np.zeros(self.num_points)

        return rho_est, a_est, b_est, w_est

    def calc_poly_surf_coeffs(self, a_est, b_est, dx, dy, dz, itv=10):
        """estimates error model using polynomial surface fitting

        This method calculates the coefficients of the polynomial-surface
        error model intended to account for the positional errors resulting
        from differences between the sensor model implemented in cBLUE and
        the unknown, proprietary manufacturer sensor model.

        The original Matlab research code used a 'fit' function with a
        'poly23' option, which is emulated here by using np.linalg.lstsq
        with terms for a, b, a^2, ab, b^2, a^2b, ab^2, and b^3

        :param a_est:
        :param b_est:
        :param dx:
        :param dy:
        :param dz:
        :param itv:
        :return: list[tuple, tuple, tuple] TODO: verify
        """

        B0 = b_est[::itv]
        A0 = a_est[::itv]

        A = np.vstack((
            ne.evaluate('A0 * 0 + 1'),
            ne.evaluate('A0'),
            ne.evaluate('B0'),
            ne.evaluate('A0 ** 2'),
            ne.evaluate('A0 * B0'),
            ne.evaluate('B0 ** 2'),
            ne.evaluate('A0 ** 2 * B0'),
            ne.evaluate('A0 * B0 ** 2'),
            ne.evaluate('B0 ** 3'))).T

        (coeffs_x, __, __, __) = np.linalg.lstsq(A, dx[::itv], rcond=None)
        (coeffs_y, __, __, __) = np.linalg.lstsq(A, dy[::itv], rcond=None)
        (coeffs_z, __, __, __) = np.linalg.lstsq(A, dz[::itv], rcond=None)
        return (coeffs_x, coeffs_y, coeffs_z, )

    @staticmethod
    def calcRMSE(data):
        """calc root mean square error for input data"""
        num_coords, num_points = data.shape
        AMDE = np.mean(np.abs(data), axis=1)  # average mean distance error
        RMSE = sqrt(sum(sum(np.square(data))) / num_points)  # root mean squares error
        logging.info('Mean Difference:\n'
                     'X: {:.3f}\n'
                     'Y: {:.3f}\n'
                     'Z: {:.3f}'.format(AMDE[0], AMDE[1], AMDE[2]))
        logging.info('RMSE: {:.3f}\n'.format(RMSE))

    def calc_diff(self, subaer_pos_pre):
        """calculate the difference between the las position and the initial cBLUE position

        This method calculates the difference between the x, y, and z components of the
        positions in the las file and the respective cBLUE-calculated position components.
        Ideally, a cBLUE-calculated position would identically match the corresponding
        position in the las file, but due to differences between the proprietary manufacturer
        sensor model and the sensor model used by cBLUE, the positions are not identical.
        The differences calculated by this method are used in the polynomial-surface error
        modeling process to correct for the errors caused by the sensor model discrepancies.

        :param subaer_pos_pre:
        :return:
        """
        # calc diff between true and est las xyz (aer_pos = Laser Estimates)
        x_las = self.x_las
        y_las = self.y_las
        z_las = self.z_las
        aer_x_pre = subaer_pos_pre[0]
        aer_y_pre = subaer_pos_pre[1]
        aer_z_pre = subaer_pos_pre[2]
        dx = ne.evaluate("x_las - aer_x_pre")
        dy = ne.evaluate("y_las - aer_y_pre")
        dz = ne.evaluate("z_las - aer_z_pre")
        return dx, dy, dz

    def calc_aer_pos_pre(self, rho_est, a_est, b_est, w_est):
        """calculates the inital cBLUE aubaerial position

        This method calculates the inital cBLUE subaerial position using the
        'lambdified' geolocation equation (without the polynomial-surface
        error terms).

        :param rho_est:
        :param a_est:
        :param b_est:
        :param w_est:
        :return:
        """
        aer_x_pre = self.fF_orig[0](a_est, b_est, self.h0, self.p0, self.r0, rho_est, w_est, self.x_sbet)
        aer_y_pre = self.fF_orig[1](a_est, b_est, self.h0, self.p0, self.r0, rho_est, w_est, self.y_sbet)
        aer_z_pre = self.fF_orig[2](a_est, b_est, self.p0, self.r0, rho_est, w_est, self.z_sbet)
        return aer_x_pre, aer_y_pre, aer_z_pre

    def calc_aer_pos(self, coeffs, a_est, b_est, aer_pos_pre):
        """calculates the final cBLUE subearial position

        This method calculates the final cBLUE subaerial position by adding
        a polynomial-surface modelled error term

        :param coeffs:
        :param a_est:
        :param b_est:
        :param aer_pos_pre:
        :return:
        """

        A = np.vstack((
            ne.evaluate('a_est * 0 + 1'),
            ne.evaluate('a_est'),
            ne.evaluate('b_est'),
            ne.evaluate('a_est ** 2'),
            ne.evaluate('a_est * b_est'),
            ne.evaluate('b_est ** 2'),
            ne.evaluate('a_est ** 2 * b_est'),
            ne.evaluate('a_est * b_est ** 2'),
            ne.evaluate('b_est ** 3'))).T

        aer_x_pre = aer_pos_pre[0]
        aer_y_pre = aer_pos_pre[1]
        aer_z_pre = aer_pos_pre[2]

        err_x = np.sum(A * coeffs[0], axis=1)
        err_y = np.sum(A * coeffs[1], axis=1)
        err_z = np.sum(A * coeffs[2], axis=1)

        aer_pos_x = ne.evaluate('aer_x_pre + err_x')
        aer_pos_y = ne.evaluate('aer_y_pre + err_y')
        aer_pos_z = ne.evaluate('aer_z_pre + err_z')
        return aer_pos_x, aer_pos_y, aer_pos_z

    def calc_aer_pos_err(self, aer_pos):
        """calculates the difference between the las and cBLUE positions

        This method calculates the differences between the x, y, and z
        components of the final cBLUE positions and the corresponding
        las file positions.

        :param aer_pos:
        :return:
        """
        aer_x = aer_pos[0]
        aer_y = aer_pos[1]
        aer_z = aer_pos[2]
        aer_x_err = ne.evaluate('aer_x - x_las')
        aer_y_err = ne.evaluate('aer_y - y_las')
        aer_z_err = ne.evaluate('aer_z - z_las')
        return [aer_x_err, aer_y_err, aer_z_err]

class Jacobian:

    def __init(self, S):
        self.OEx = S.obs_eq[0]  # S is SensorModel object
        self.OEy = S.obs_eq[1]
        self.OEz = S.obs_eq[2]
        self.Jx, self.Jy, self.Jz  = form_jacobian()
        self.lJx, self.lJy, self.lJz = self.lambdify_jacobian()

    def form_jacobian(self):
        """generate the jacobian of the specified geolocation equation

        This method generates the Jacobian (i.e., the matrix of partial
        derivatives with respect to component variables) of the specified
        geoloation equation using the sympy symbolic math package.  Using
        sympy to symbolically calculate the Jacobian simplifies the coding
        of what would otherwise be very long equations.

        :param F1:
        :param F2:
        :param F3:
        :return: (function, function, function)
        """

        a, b, r, p, h, x, y, z, rho = symbols('a b r p h x y z rho')

        v = Matrix([a, b, r, p, h, x, y, z, rho])  # vector of unknowns
        Jx = Matrix([self.OEx]).jacobian(v)
        Jy = Matrix([self.OEy]).jacobian(v)
        Jz = Matrix([self.OEz]).jacobian(v)

        return Jx, Jy, Jz

    def lambdify_jacobian(self, eval_type='numexpr'):
        """turn the symbolical Jacobian into a function for faster computation

        This method "lambdifies" (or "functionizes") the Jacobian components, for
        faster calculations. Part of this lambdify process includes simplifying
        the numerous trigonometric calculations of the Jacobian by defining the
        Jacobian functions to be functions of the sines and cosines of the various
        parameters, instead of the parameters directly.

        Reference:
        https://docs.sympy.org/latest/modules/utilities/lambdify.html

        :param Jx:
        :param Jy:
        :param Jz:
        :param eval_type:
        :return: (function, function, function)
        """

        # create variables for symbolic computations
        a, b, w, r, p, h, rho, \
        p00, p10, p01, p20, p11, p02, p21, p12, p03, \
        sin_a, sin_b, sin_w, sin_r, sin_p, sin_h, \
        cos_a, cos_b, cos_w, cos_r, cos_p, cos_h \
            = symbols('a b w r p h rho '
                      'p00 p10 p01 p20 p11 p02 p21 p12 p03 '
                      'sin_a sin_b sin_w sin_r sin_p sin_h '
                      'cos_a cos_b cos_w cos_r cos_p cos_h')

        '''functionize the trig terms of the Jacobian x component'''
        Jxsub = []
        for i, j in enumerate(self.Jx):
            Jxsub.append(j.subs([
                (sin(a), sin_a),
                (sin(b), sin_b),
                (sin(w), sin_w),
                (sin(r), sin_r),
                (sin(p), sin_p),
                (sin(h), sin_h),
                (cos(a), cos_a),
                (cos(b), cos_b),
                (cos(w), cos_w),
                (cos(r), cos_r),
                (cos(p), cos_p),
                (cos(h), cos_h)]))

        '''functionize the trig terms of the Jacobian y component'''
        Jysub = []
        for i, j in enumerate(self.Jy):
            Jysub.append(j.subs([
                (sin(a), sin_a),
                (sin(b), sin_b),
                (sin(w), sin_w),
                (sin(r), sin_r),
                (sin(p), sin_p),
                (sin(h), sin_h),
                (cos(a), cos_a),
                (cos(b), cos_b),
                (cos(w), cos_w),
                (cos(r), cos_r),
                (cos(p), cos_p),
                (cos(h), cos_h)]))

        '''functionize the trig terms of the Jacobian z component'''
        Jzsub = []
        for i, j in enumerate(self.Jz):
            Jzsub.append(j.subs([
                (sin(a), sin_a),
                (sin(b), sin_b),
                (sin(w), sin_w),
                (sin(r), sin_r),
                (sin(p), sin_p),
                (sin(h), sin_h),
                (cos(a), cos_a),
                (cos(b), cos_b),
                (cos(w), cos_w),
                (cos(r), cos_r),
                (cos(p), cos_p),
                (cos(h), cos_h)]))

        '''functionize the x component'''
        Jxsub0_vars = (a, b, rho, p10, p21, p12, p11, p20,
                       sin_a, sin_b, sin_w, sin_r, sin_p, sin_h,
                       cos_a, cos_b, cos_w, cos_r, cos_p, cos_h)

        Jxsub1_vars = (a, b, rho, p02, p03, p21, p12, p01, p11,
                       sin_b, sin_w, sin_r, sin_p, sin_h,
                       cos_a, cos_b, cos_w, cos_r, cos_p, cos_h)

        Jxsub2_vars = (rho, sin_a, sin_b, sin_w, sin_r, sin_p, sin_h,
                       cos_a, cos_b, cos_w, cos_r, cos_h)

        Jxsub3_vars = (rho, sin_a, sin_b, sin_w, sin_r, sin_p,
                       cos_a, cos_b, cos_w, cos_r, cos_p, cos_h)

        Jxsub4_vars = (rho, sin_a, sin_b, sin_w, sin_r, sin_p, sin_h,
                       cos_a, cos_b, cos_w, cos_r, cos_p, cos_h)

        Jxsub5_vars = ()
        Jxsub6_vars = ()
        Jxsub7_vars = ()

        Jxsub8_vars = (sin_a, sin_b, sin_w, sin_r, sin_p, sin_h,
                       cos_a, cos_b, cos_w, cos_r, cos_p, cos_h)

        fJxsub0 = lambdify(Jxsub0_vars, Jxsub[0], eval_type)
        fJxsub1 = lambdify(Jxsub1_vars, Jxsub[1], eval_type)
        fJxsub2 = lambdify(Jxsub2_vars, Jxsub[2], eval_type)
        fJxsub3 = lambdify(Jxsub3_vars, Jxsub[3], eval_type)
        fJxsub4 = lambdify(Jxsub4_vars, Jxsub[4], eval_type)
        fJxsub5 = lambdify(Jxsub5_vars, Jxsub[5], eval_type)
        fJxsub6 = lambdify(Jxsub6_vars, Jxsub[6], eval_type)
        fJxsub7 = lambdify(Jxsub7_vars, Jxsub[7], eval_type)
        fJxsub8 = lambdify(Jxsub8_vars, Jxsub[8], eval_type)

        '''functionize the y component'''
        Jysub0_vars = (a, b, rho, p10, p21, p12, p11, p20,
                       sin_a, sin_b, sin_w, sin_r, sin_p, sin_h,
                       cos_a, cos_b, cos_w, cos_r, cos_p, cos_h)

        Jysub1_vars = (a, b, rho, p02, p03, p21, p12, p01, p11,
                       sin_b, sin_w, sin_r, sin_p, sin_h,
                       cos_a, cos_b, cos_w, cos_r, cos_p, cos_h)

        Jysub2_vars = (rho, sin_a, sin_b, sin_w, sin_r, sin_p, sin_h,
                       cos_a, cos_b, cos_w, cos_r, cos_h)

        Jysub3_vars = (rho, sin_a, sin_b, sin_w, sin_r, sin_p, sin_h,
                       cos_a, cos_b, cos_w, cos_r, cos_p)

        Jysub4_vars = (rho, sin_a, sin_b, sin_w, sin_r, sin_p, sin_h,
                       cos_a, cos_b, cos_w, cos_r, cos_p, cos_h)

        Jysub5_vars = ()
        Jysub6_vars = ()
        Jysub7_vars = ()

        Jysub8_vars = (sin_a, sin_b, sin_w, sin_r, sin_p, sin_h,
                       cos_a, cos_b, cos_w, cos_r, cos_p, cos_h)

        fJysub0 = lambdify(Jysub0_vars, Jysub[0], eval_type)
        fJysub1 = lambdify(Jysub1_vars, Jysub[1], eval_type)
        fJysub2 = lambdify(Jysub2_vars, Jysub[2], eval_type)
        fJysub3 = lambdify(Jysub3_vars, Jysub[3], eval_type)
        fJysub4 = lambdify(Jysub4_vars, Jysub[4], eval_type)
        fJysub5 = lambdify(Jysub5_vars, Jysub[5], eval_type)
        fJysub6 = lambdify(Jysub6_vars, Jysub[6], eval_type)
        fJysub7 = lambdify(Jysub7_vars, Jysub[7], eval_type)
        fJysub8 = lambdify(Jysub8_vars, Jysub[8], eval_type)

        '''functionize the z component'''
        Jzsub0_vars = (a, b, rho, p10, p21, p12, p11, p20,
                       sin_a, sin_b, sin_w, sin_r, sin_p,
                       cos_a, cos_b, cos_w, cos_r, cos_p)

        Jzsub1_vars = (a, b, rho, p02, p03, p21, p12, p01, p11,
                       sin_b, sin_w, sin_r, sin_p,
                       cos_a, cos_b, cos_w, cos_r, cos_p)

        Jzsub2_vars = (rho, sin_a, sin_b, sin_w, sin_r,
                       cos_a, cos_b, cos_w, cos_r, cos_p)

        Jzsub3_vars = (rho, sin_a, sin_b, sin_w, sin_r, sin_p,
                       cos_a, cos_b, cos_w, cos_r, cos_p)

        Jzsub4_vars = ()
        Jzsub5_vars = ()
        Jzsub6_vars = ()
        Jzsub7_vars = ()

        Jzsub8_vars = (sin_a, sin_b, sin_w, sin_r, sin_p,
                       cos_a, cos_b, cos_w, cos_r, cos_p)

        fJzsub0 = lambdify(Jzsub0_vars, Jzsub[0], eval_type)
        fJzsub1 = lambdify(Jzsub1_vars, Jzsub[1], eval_type)
        fJzsub2 = lambdify(Jzsub2_vars, Jzsub[2], eval_type)
        fJzsub3 = lambdify(Jzsub3_vars, Jzsub[3], eval_type)
        fJzsub4 = lambdify(Jzsub4_vars, Jzsub[4], eval_type)
        fJzsub5 = lambdify(Jzsub5_vars, Jzsub[5], eval_type)
        fJzsub6 = lambdify(Jzsub6_vars, Jzsub[6], eval_type)
        fJzsub7 = lambdify(Jzsub7_vars, Jzsub[7], eval_type)
        fJzsub8 = lambdify(Jzsub8_vars, Jzsub[8], eval_type)

        '''group the functioned jacobian components'''
        lJx = [fJxsub0, fJxsub1, fJxsub2, fJxsub3, fJxsub4, fJxsub5, fJxsub6, fJxsub7, fJxsub8]
        lJy = [fJysub0, fJysub1, fJysub2, fJysub3, fJysub4, fJysub5, fJysub6, fJysub7, fJysub8]
        lJz = [fJzsub0, fJzsub1, fJzsub2, fJzsub3, fJzsub4, fJzsub5, fJzsub6, fJzsub7, fJzsub8]

        return lJx, lJy, lJz

    def calc_trig_terms(self, a_est, b_est, r0, p0, h0):
        """evaluates the trigonometric terms in the Jacobian

        This method aims to simplify evaluation of the Jacobian by pre-evaluating
        the trigonometic terms of the Jacobian.  The reasoning is that this speeds
        up the computations because the trigonometric terms are only evaluated
        once, instead of every time they show up in the Jacobian.

        :param a_est:
        :param b_est:
        :param r0:
        :param p0:
        :param h0:
        :return:
        """

        sin_a0 = ne.evaluate("sin(a_est)")  # uses passed parameter
        sin_b0 = ne.evaluate("sin(b_est)")  # uses passed parameter
        sin_w0 = np.zeros(self.num_points)  # ne.evaluate("sin(w_est)") ... sin(0) = 0
        sin_r0 = ne.evaluate("sin(r0)")  # uses passed parameter
        sin_p0 = ne.evaluate("sin(p0)")  # uses passed parameter
        sin_h0 = ne.evaluate("sin(h0)")  # uses passed parameter
        cos_a0 = ne.evaluate("cos(a_est)")  # uses passed parameter
        cos_b0 = ne.evaluate("cos(b_est)")  # uses passed parameter
        cos_w0 = np.ones(self.num_points)  # ne.evaluate("cos(w_est)") ... cos(0) = 1
        cos_r0 = ne.evaluate("cos(r0)")  # uses passed parameter
        cos_p0 = ne.evaluate("cos(p0)")  # uses passed parameter
        cos_h0 = ne.evaluate("cos(h0)")  # uses passed parameter
        return (sin_a0, sin_b0, sin_w0, sin_r0, sin_p0, sin_h0,
                cos_a0, cos_b0, cos_w0, cos_r0, cos_p0, cos_h0)

    def eval_jacobian(self, data):
        """evaluate the Jacobian of the modified laser geolocation equation

        This method evaluates the Jacobian by passing the relevant parameters
        to the lambdified functions representing the x, y, and z components
        of the Jacobian.

        To simplify the computations, the trigonometric terms are pre-evaluated and
        are represented by the following variables:
        sa = sin(a0)
        sb = sin(b0)
        sw = sin(w0)
        sr = sin(r0)
        sp = sin(p0)
        sh = sin(h0)
        ca = cos(a0)
        cb = cos(b0)
        cw = cos(w0)
        cr = cos(r0)
        cp = cos(p0)
        ch = cos(h0)

        :param rho_est:
        :param a_est:
        :param b_est:
        :param coeffs:
        :return:
        """

        sa, sb, sw, sr, sp, sh, ca, cb, cw, cr, cp, ch \
            = self.calc_trig_terms(a_est, b_est, self.r0, self.p0, self.h0)

        rho_est, a_est, b_est, __ = self.S.estimate_rho_a_b()

        coeffs = self.calc_poly_surf_coeffs()

        p00x, p10x, p01x, p20x, p11x, p02x, p21x, p12x, p03x = coeffs[0]
        p00y, p10y, p01y, p20y, p11y, p02y, p21y, p12y, p03y = coeffs[1]
        p00z, p10z, p01z, p20z, p11z, p02z, p21z, p12z, p03z = coeffs[2]

        '''evaluate the x component'''
        Jx = np.vstack(
            (self.J.lJx[0](a_est, b_est, rho_est, p10x, p21x, p12x, p11x, p20x,
                         sa, sb, sw, sr, sp, sh, ca, cb, cw, cr, cp, ch),
             self.J.lJx[1](a_est, b_est, rho_est, p02x, p03x, p21x, p12x, p01x, p11x,
                         sb, sw, sr, sp, sh, ca, cb, cw, cr, cp, ch),
             self.J.lJx[2](rho_est, sa, sb, sw, sr, sp, sh, ca, cb, cw, cr, ch),
             self.J.lJx[3](rho_est, sa, sb, sw, sr, sp, ca, cb, cw, cr, cp, ch),
             self.J.lJx[4](rho_est, sa, sb, sw, sr, sp, sh, ca, cb, cw, cr, cp, ch),
             np.ones(self.num_points),
             self.J.lJx[8](sa, sb, sw, sr, sp, sh, ca, cb, cw, cr, cp, ch)))

        '''evaluate the y component'''
        Jy = np.vstack(
            (self.J.lJy[0](a_est, b_est, rho_est, p10y, p21y, p12y, p11y, p20y,
                         sa, sb, sw, sr, sp, sh, ca, cb, cw, cr, cp, ch),
             self.J.lJy[1](a_est, b_est, rho_est, p02y, p03y, p21y, p12y, p01y, p11y,
                         sb, sw, sr, sp, sh, ca, cb, cw, cr, cp, ch),
             self.J.lJy[2](rho_est, sa, sb, sw, sr, sp, sh, ca, cb, cw, cr, ch),
             self.J.lJy[3](rho_est, sa, sb, sw, sr, sp, sh, ca, cb, cw, cr, cp),
             self.J.lJy[4](rho_est, sa, sb, sw, sr, sp, sh, ca, cb, cw, cr, cp, ch),
             np.ones(self.num_points),
             self.J.lJy[8](sa, sb, sw, sr, sp, sh, ca, cb, cw, cr, cp, ch)))

        '''evaluate the z component'''
        Jz = np.vstack(
            (self.J.lJz[0](a_est, b_est, rho_est, p10z, p21z, p12z, p11z, p20z,
                         sa, sb, sw, sr, sp, ca, cb, cw, cr, cp),
             self.J.lJz[1](a_est, b_est, rho_est, p02z, p03z, p21z, p12z, p01z, p11z,
                         sb, sw, sr, sp, ca, cb, cw, cr, cp),
             self.J.lJz[2](rho_est, sa, sb, sw, sr, ca, cb, cw, cr, cp),
             self.J.lJz[3](rho_est, sa, sb, sw, sr, sp, ca, cb, cw, cr, cp),
             np.ones(self.num_points),
             self.J.lJz[8](sa, sb, sw, sr, sp, ca, cb, cw, cr, cp)))

        return (Jx, Jy, Jz, )


class Subaerial:

    def __init__(self, S, J, D):
        """
        :param List[ndarray] D: the merged data

        The following table lists the contents of D:

        =====   =========   =======================
        Index   ndarray     description
        =====   =========   =======================
        0       t_sbet      sbet timestamps
        1       t_las       las timestamps
        2       x_las       las x coordinates
        3       y_las       las y coordinates
        4       z_las       las z coordinates
        5       x_sbet      sbet x coordinates
        6       y_sbet      sbet y coordinates
        7       z_sbet      sbet z coordinates
        8       r           sbet roll
        9       p           sbet pitch
        10      h           sbet heading
        11      std_ang1    ang1 uncertainty
        12      std_ang2    ang2 uncertainty
        13      std_r       sbet roll uncertainty
        14      std_p       sbet pitch uncertainty
        15      std_h       sbet heading uncertainty
        16      stdx_sbet   sbet x uncertainty
        17      stdy_sbet   sbet y uncertainty
        18      stdz_sbet   sbet z uncertainty
        19      std_rho     ?
        =====   =========   =======================
        """

        self.S = S  # SensorModel object
        self.J = J  # Jacobian object
        self.x_las = D[2]
        self.y_las = D[3]
        self.z_las = D[4]
        self.x_sbet = D[5]
        self.y_sbet = D[6]
        self.z_sbet = D[7]
        self.r0 = D[8]
        self.p0 = D[9]
        self.h0 = D[10]
        self.C = np.asarray(D[11:])
        self.is_empty = not D
        self.num_points = self.x_las.shape
        self.aer_cols = None

    def propogate_uncertainty(self, J_eval):
        """propogates the subaerial uncertatinty

        This method propogates the uncertainty of the component uncertainties
        using the following equation:

        TODO: insert latex

        :param pJ1:
        :param pJ2:
        :param pJ3:
        :return: (ndarray, ndarray, list[str])
        """

        C = self.C
        C = ne.evaluate("C * C")  # variance = stddev**2

        # delete the rows corresponding to the Jacobian functions that equal 0
        Cx = np.delete(C, [6, 7], 0)
        Cy = np.delete(C, [5, 7], 0)
        Cz = np.delete(C, [4, 5, 6], 0)

        Jx = J_eval[0]
        Jy = J_eval[1]
        Jz = J_eval[2]

        sum_Jx = ne.evaluate("sum(Jx * Jx * Cx, axis=0)")
        sum_Jy = ne.evaluate("sum(Jy * Jy * Cy, axis=0)")
        sum_Jz = ne.evaluate("sum(Jz * Jz * Cz, axis=0)")

        sx = ne.evaluate("sqrt(sum_Jx)")
        sy = ne.evaluate("sqrt(sum_Jy)")
        aer_tvu = ne.evaluate("sqrt(sum_Jz)")
        aer_thu = ne.evaluate('sqrt(sx**2 + sy**2)')

        return aer_thu, aer_tvu, ['subaerial_thu', 'subaerial_tvu']

    def calc_subaerial_tpu(self):
        """calculates the subaerial uncertainty

        This method calculates the subaerial uncertainty through four major
        steps:

        1) Evaluate the preliminary geolocation equation
            First, a preliminary position for each data point is calculated
            using the preliminary geolocation equation (i.e., the one
            without the polynomial-surface error terms).  The preliminary
            positions are not expected to match the corresponding positions
            in the las file because the sensor model implemented in cBLUE
            is only an approximation of the unknown, proprietary
            manufacturer sensor model.

        2) Calculate and apply the polynomial-surface error coefficients
            Second, the position errors resulting from the differences
            between the sensor model implemented in cBLUE and the unknown,
            proprietary manufacturer sensor model are accounted for with
            polynomial-surface error modeling.  The coefficients of the
            error model are calculated using a least squares calculation
            intended to be equivalent to Matlab's fit(poly23) function,
            which was used in the original Matlab research code.

        3) Evaluate the Jacobian
            Third, the Jacobian of the modified laser geolocation equation,
            (i.e., the one with the polynomial-surface error terms)

        4) Propagate Uncertainty

        :return:
        """
        if self.is_empty:  # i.e., if D is empty (las and sbet not merged)
            logging.warning('SBET and LAS not merged because max delta '
                            'time exceeded acceptable threshold of {} '
                            'sec(s).'.format(Merge.dt_threshold))
        else:

            '''1) Evaluate the preliminary geolocation equation'''
            rho_est, a_est, b_est, w_est = self.estimate_rho_a_b()
            aer_pos_pre = self.calc_aer_pos_pre(rho_est, a_est, b_est, w_est)
            dx, dy, dz = self.calc_diff(aer_pos_pre)


            '''3) Evaluate the Jacobian'''
            J_eval = self.J.eval_jacobian()

            '''4) Propagate Uncertainty'''
            aer_thu, aer_tvu, self.aer_cols = self.propogate_uncertainty(J_eval)

            return np.vstack((aer_thu, aer_tvu)).T, self.aer_cols


if __name__ == '__main__':
    pass
