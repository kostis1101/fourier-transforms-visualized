from svgpathtools import svg2paths, Path, Line, CubicBezier # pip install svgpathtools 
import tkinter as tk
import math
from tkinter import filedialog
import threading
from tkinter import simpledialog

class App:
	def __init__(self, root):
		self.root = root
		self.size = .3 # size of preview
		self.offset = [100, 300] # offset of preview
		self.detail = 401
		self.is_running = True
		self.coefficients = {}
		self.speed = 0.005 # speed of the simulation
		self.last_resulting_point = ''
		self.file_name = filedialog.askopenfile().name # gets file (.svg only)
		# movement
		self.root.bind('w', lambda event, direction=[0, 10]: self.move(e=event, direction=direction))
		self.root.bind('a', lambda event, direction=[10, 0]: self.move(e=event, direction=direction))
		self.root.bind('s', lambda event, direction=[0, -10]: self.move(e=event, direction=direction))
		self.root.bind('d', lambda event, direction=[-10, 0]: self.move(e=event, direction=direction))

		self.root.bind('<Control-o>', self.open_file)
		
		start_thread = threading.Thread(target=self.widgets)
		start_thread.start()


	def open_file(self, e):
		#opening a file and loading all the neseccary data
		self.file_name = filedialog.askopenfile().name
		self.is_running = False

		self.canvas.delete('all')
		self.get_points()
		self.draw()
		self.coefficients = {}
		self.last_resulting_point = ''
		self.get_coefficients()

		self.t = 0
		self.animations()
		self.is_running = True

	def move(self, e, direction):
		# move the preview (changes the offset)
		self.offset[0] += direction[0]
		self.offset[1] += direction[1]

		for line in self.drawed_lines:
			self.canvas.coords(line,
				self.canvas.coords(line)[0] + direction[0], 
				self.canvas.coords(line)[1] + direction[1], 
				self.canvas.coords(line)[2] + direction[0], 
				self.canvas.coords(line)[3] + direction[1])

	def change_zoom(self):
		self.size = simpledialog.askfloat('zoom', 'change zoom level to: ')
		self.drawed_lines = []
		self.canvas.delete('all')

	def widgets(self):
		# creates all the widgets
		self.canvas = tk.Canvas(self.root, bg='black')
		self.canvas.pack(expand=1, fill='both')
		self.root.geometry('1000x1000')

		self.menu = tk.Menu(self.root)
		self.root.config(menu=self.menu)

		self.open_menu = self.menu.add_cascade(label='Open', command=lambda: self.open_file(None))
		self.open_menu = self.menu.add_cascade(label='Zoom', command=self.change_zoom)

		self.get_points()
		self.draw()
		self.get_coefficients()

		self.t = 0 # the time variable
		self.animations()

	def get_points(self):
		# gets all the points on the path

		paths, attributes = svg2paths(self.file_name)
		paths = paths[0]

		self.points_array = []
		self.points = {}

		NUM_SAMPLES = 20 # detail of points

		for path in paths:
			for i in range(NUM_SAMPLES):
				self.points_array.append(path.point(i/(NUM_SAMPLES-1)))

		for i, point in enumerate(self.points_array):
			self.points[i/(len(self.points_array) - 1)] = point

	def draw(self):
		self.lines = []
		for i in range(len(self.points_array)):
			if i != len(self.points_array) - 1:
				self.lines.append(self.canvas.create_line(\
					self.points_array[i].real * self.size + self.offset[0], 
					self.points_array[i].imag * self.size + self.offset[1], 
					self.points_array[i + 1].real * self.size + self.offset[0], 
					self.points_array[i + 1].imag * self.size + self.offset[1]
				))

		self.drawed_lines = []

	def get_coefficients(self):
		# calculates coefficients for all the rotating vectors.
		# This determines the starting rotation and the length of the vector

		for i in range(int((-self.detail - 1) / 2) + 1, int((self.detail - 1) / 2) + 1):
			self.coefficients[i] = self.intergral(i)

		_coefficients = self.coefficients

		self.coefficients = {}

		for i in range(int((self.detail - 1) / 2) + 1):
			self.coefficients[i] = _coefficients[i]
			self.coefficients[-i] = _coefficients[-i]

	def intergral(self, n):
		# calculates the intergral, needed to find coefficients

		result = 0
		for t in self.points:
			result += self.points[t] * (math.e ** (-n * 2 * math.pi * 1j * t)) * (1 / len(self.points))
		return result

	def animations(self):
		# main animations the runs every 50ms

		resulting_point = 0
		last_point = 0

		self.canvas.delete('vectors')

		for n in self.coefficients:
			c = self.coefficients[n]
			resulting_point += c * (math.e ** (n * 2 * math.pi * self.t * 1j))

			if n != 0:
				self.create_arrow(resulting_point.real * self.size + self.offset[0],
					resulting_point.imag * self.size + self.offset[1],
					last_point.real * self.size + self.offset[0],
					last_point.imag * self.size + self.offset[1],)
			last_point = resulting_point

		if self.last_resulting_point != '' and self.last_resulting_point != (935.4909844885157+2026.3038727261635j):
			self.drawed_lines.append(self.canvas.create_line(
				self.last_resulting_point.real * self.size + self.offset[0],
				self.last_resulting_point.imag * self.size + self.offset[1],
				resulting_point.real * self.size + self.offset[0],
				resulting_point.imag * self.size + self.offset[1],
				fill='blue', width=2)
			)

		for i, line in enumerate(self.drawed_lines):
			self.canvas.itemconfig(line, fill='#%02x%02x%02x' % (0, 0, int(255 * (i / len(self.drawed_lines)))))

		if len(self.drawed_lines) > 200:
			self.canvas.delete(self.drawed_lines[0])
			self.drawed_lines.pop(0)

		self.last_resulting_point = resulting_point

		self.t += self.speed
		self.t = self.t % 1

		self.t = (round(self.t * 10000) // (self.speed * 10000)) * self.speed
		if self.t == 0:
			print(self.t)
			self.t = self.speed * 2
		# self.last_t = self.t
		if self.is_running:
			self.canvas.after(50, self.animations)

	def create_arrow(self, x1, y1, x2, y2):
		# creates an arrow to visualize each vector

		arrow_size = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
		self.canvas.create_line(x1, y1, x2, y2, tags='vectors', fill='#AAAAAA', width=arrow_size*0.2)
		angle = math.atan((y2 - y1) / (x2 - x1))
		direction = 5
		if x1 < x2:
			direction = 1
		angle1 = angle - math.pi * direction / 6
		angle2 = angle + math.pi * direction / 6
		arrow_size = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
		points = [x1, y1, x1 + math.cos(angle1) * arrow_size, y1 + math.sin(angle1) * arrow_size, x1 + math.cos(angle2) * arrow_size, y1 + math.sin(angle2) * arrow_size]
		self.canvas.create_polygon(points, fill='white', tag='vectors')


w = tk.Tk()
App(w)
w.mainloop()