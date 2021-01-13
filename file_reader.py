import os
import sys

class FileReader:

	def __init__(self):
		pass

	def get(self, filepath, cookies):
		# '''
		#  Returns a binary string of the file contents, or None.
		#  '''
		#Does the lookup of the file and encodes it in binary
		try:
			f = open(filepath, 'rb')
			toReturn = f.read()
			f.close()
			#print("File read correctly")
			return toReturn
		except: #Either doesn't exist or is a directory
			if(self.head(filepath, cookies) == None):
				#print("File failed to be read, thinks that it isn't a valid path")
				return None
			else:
				toReturn = '<html><body><h1>' + filepath + '</h1></body></html>'
				#res = ''.join(format(ord(i), 'b') for i in toReturn)
				#res = ''.join(format(ord(x), 'b') for x in toReturn)
				#print("File wasn't read, thinks its a directory")
				return toReturn



	def head(self, filepath, cookies):

		try:

			size = os.path.getsize(filepath)

			return size
		except (FileNotFoundError, OSError): #doesn't exist
			return None

