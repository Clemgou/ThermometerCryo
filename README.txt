Required python module:
	- numpy
	- PyQt5
	- time
	- scipy
	- pyqtgraph ( attention need the latest git version, because the older one uses the 'clock' function from 'time' module, which no longer exists since version python-3.7.7)
	  latest version with: pip install git+https://github.com/pyqtgraph/pyqtgraph@develop
	(- pyopengl  ( for pyqtgraph.opengl ) NOT NECESSARY ANYMORE)


TO DO:
        - ResistanceProbe_class using a stream package
        - Make Conversion functions that are more versatile (accept np.arrays), and without optimization algorithms
        - combo box to display all temperature plot in parallel
        - Save function, with continuous mode, or that update according to the buffer size, ...
        - ...