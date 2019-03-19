import os

#from pathos.multiprocessing import ProcessingPool as Pool
import pathos.pools as pp


class myClass:
	def __init__(self):
		pass

	def square(self, x):
		print(x*x)

	def run(self, inList):
		pool = Pool().map
		result = pool(self.square, inList)
		print(result)

	def run_tpu_multiprocess(self, sbet_las_generator):
		"""runs the tpu calculations using multiprocessing

		This methods initiates the tpu calculations using the pathos multiprocessing
		framework (https://pypi.org/project/pathos/).  Whether the tpu calculations
		are done with multiprocessing or not is currently determined by which
		"run_tpu_*" method is manually specified in the tpu_process_callback()
		method of the CBlueApp class.  Including a user option to select single
		processing or multiprocessing is deferred to future versions.

		:param sbet_las_generator:
		:return:
		"""
		p = pp.ProcessPool(4)
		p.map(self.square, sbet_las_generator)
		p.close()
		p.join()


if __name__== '__main__' :
	m = myClass()
	m.run_tpu_multiprocess(range(10))