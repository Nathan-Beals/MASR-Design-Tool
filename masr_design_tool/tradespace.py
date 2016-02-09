try:
    from Tkinter import *
except ImportError:
    from tkinter import *
import ttk
from winplace import get_win_place
from vehicle import Vehicle
from unitconversion import convert_unit
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
from matplotlib.backend_bases import key_press_handler
from matplotlib import rcParams
rcParams.update({'figure.autolayout': True})
from mpl_toolkits.mplot3d import Axes3D


class Tradespace(Toplevel):
    def __init__(self, master):
        Toplevel.__init__(self, master)
        self.master = master
        self.title('Tradespace')

        # Place window
        xpos, ypos = get_win_place(self)
        self.geometry('+%d+%d' % (xpos, ypos))

        # Load alternatives from oo_quad_GUI.AlternativesFrame
        self.f_alts = self.master.f_alternatives
        self.alts = self.master.alternatives

        # Load vehicle performance attribute info
        self.attr_dict = Vehicle.perf_attr_dict
        self.attr_names = Vehicle.perf_attr_names

        # Create mainframe and subframes
        self.mainframe = ttk.Frame(self, padding=5)
        self.env_frame = EnvelopePlot(self)
        self.var_distr_frame = VariableDistrPlot(self)
        self.button_frame = ttk.Frame(self.mainframe, padding=5)

        # Create button frame widgets
        self.close_button = ttk.Button(self.button_frame, text='Close', command=self.destroy)
        self.new_ts_win = ttk.Button(self.button_frame, text='Open another tradespace window', command=self.open_ts_win)
        self.plot_select_label = ttk.Label(self.button_frame, text='Select plots to view')
        self.env_frame_var = IntVar()
        self.env_frame_var.set(1)
        self.env_frame_check = ttk.Checkbutton(self.button_frame, variable=self.env_frame_var, text='Design Envelope',
                                               command=self.plot_selected)
        self.var_distr_var = IntVar()
        self.var_distr_var.set(1)
        self.var_distr_check = ttk.Checkbutton(self.button_frame, variable=self.var_distr_var,
                                               text='1 Perf Requirement for all Alts', command=self.plot_selected)

        # Place everything
        self.plot_select_label.pack()
        self.env_frame_check.pack(pady=5)
        self.var_distr_check.pack(pady=5)
        self.close_button.pack(side=RIGHT, padx='3 5')
        self.new_ts_win.pack(side=RIGHT, padx='5 3')

        self.mainframe.pack()

        self.env_frame.pack(side=LEFT, fill=BOTH, expand=1)
        self.var_distr_frame.pack(side=LEFT, fill=BOTH, expand=1)
        self.button_frame.pack(fill=Y, side=RIGHT)

    def plot_selected(self):
        self.button_frame.pack_forget()
        self.env_frame.pack_forget()
        self.var_distr_frame.pack_forget()
        if self.env_frame_var.get():
            self.env_frame.pack(side=LEFT, fill=BOTH, expand=1)
        if self.var_distr_var.get():
            self.var_distr_frame.pack(side=LEFT, fill=BOTH, expand=1)
        self.button_frame.pack(fill=Y, side=RIGHT)

    def open_ts_win(self):
        Tradespace(self.master)


class EnvelopePlot(ttk.Frame):
    def __init__(self, master):
        ttk.Frame.__init__(self, master, padding=5)
        self.master = master

        # Create plot frame and options frame
        self.plot_frame = ttk.Frame(self, padding=5)
        self.options_frame = ttk.Frame(self, padding=5)

        # Create options frame widgets
        self.xaxis_choice_label = ttk.Label(self.options_frame, text='X-axis quantity')
        self.yaxis_choice_label = ttk.Label(self.options_frame, text='Y-axis quantity')
        self.zaxis_choice_label = ttk.Label(self.options_frame, text='Z-axis quantity')

        self.xaxis_var = StringVar()
        self.xaxis_cb = ttk.Combobox(self.options_frame, textvariable=self.xaxis_var,
                                     values=self.master.attr_dict.keys(), state='readonly')
        self.xaxis_cb.current(0)
        self.xaxis_cb.bind("<<ComboboxSelected>>", self.change_axis_var_event)
        self.yaxis_var = StringVar()
        self.yaxis_cb = ttk.Combobox(self.options_frame, textvariable=self.yaxis_var,
                                     values=self.master.attr_dict.keys(), state='readonly')
        self.yaxis_cb.current(1)
        self.yaxis_cb.bind("<<ComboboxSelected>>", self.change_axis_var_event)
        self.zaxis_var = StringVar()
        self.zaxis_cb = ttk.Combobox(self.options_frame, textvariable=self.zaxis_var,
                                     values=self.master.attr_dict.keys(), state='readonly')
        self.zaxis_cb.current(2)
        self.zaxis_cb.bind("<<ComboboxSelected>>", self.change_axis_var_event)

        self.xaxis_unit_var = StringVar()
        self.xaxis_unit_cb = ttk.Combobox(self.options_frame, textvariable=self.xaxis_unit_var,
                                          values=self.master.attr_dict[self.xaxis_var.get()], width=4, state='readonly')
        self.xaxis_unit_cb.current(0)
        self.xaxis_unit_cb.bind("<<ComboboxSelected>>", self.plot3d)
        self.yaxis_unit_var = StringVar()
        self.yaxis_unit_cb = ttk.Combobox(self.options_frame, textvariable=self.yaxis_unit_var,
                                          values=self.master.attr_dict[self.yaxis_var.get()], width=4, state='readonly')
        self.yaxis_unit_cb.current(0)
        self.yaxis_unit_cb.bind("<<ComboboxSelected>>", self.plot3d)
        self.zaxis_unit_var = StringVar()
        self.zaxis_unit_cb = ttk.Combobox(self.options_frame, textvariable=self.zaxis_unit_var,
                                          values=self.master.attr_dict[self.zaxis_var.get()], width=4, state='readonly')
        self.zaxis_unit_cb.current(0)
        self.zaxis_unit_cb.bind("<<ComboboxSelected>>", self.plot3d)

        self.dataclick_var = IntVar()
        self.dataclick_check = ttk.Checkbutton(self.options_frame, text="Activate selectable data points",
                                               variable=self.dataclick_var)
        self.pt3Dshow_var = IntVar()
        self.pt3Dshow_check = ttk.Checkbutton(self.options_frame, text='Show 3D points', variable=self.pt3Dshow_var,
                                              command=self.plot3d)
        self.pt3Dshow_var.set(1)
        self.ptprojections_var = IntVar()
        self.ptprojections_check = ttk.Checkbutton(self.options_frame, text='Show 2D point projections',
                                                   variable=self.ptprojections_var, command=self.plot3d)

        # Create plot frame widgets
        self.fig = Figure(figsize=(6, 5), dpi=100)
        self.ax3d = self.fig.add_subplot(111, projection='3d')

        self.ax3d.set_axisbelow(True)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.show()
        Axes3D.mouse_init(self.ax3d)
        self.canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)

        # Set up storage variable to hold the last pick event (see self.plot3d.pick_handler for details)
        self.last_pick_event = matplotlib.backend_bases.PickEvent

        # Call plot3d for the first time
        self.plot3d()

        # Create toolbar for the envelope plot
        self.toolbar = NavigationToolbar2TkAgg(self.canvas, self.plot_frame)
        self.toolbar.update()
        self.canvas._tkcanvas.pack(side=TOP, fill=BOTH, expand=1)

        # Grid options frame widgets
        self.xaxis_choice_label.grid(column=0, row=0, columnspan=2, padx=5, pady=5)
        self.xaxis_cb.grid(column=0, row=1, padx=5, pady='2 5')
        self.xaxis_unit_cb.grid(column=1, row=1, padx='0 5', pady='2 5')

        self.yaxis_choice_label.grid(column=0, row=2, columnspan=2, padx=5, pady=5)
        self.yaxis_cb.grid(column=0, row=3, padx=5, pady='2 5')
        self.yaxis_unit_cb.grid(column=1, row=3, padx='0 5', pady='2 5')

        self.zaxis_choice_label.grid(column=0, row=4, columnspan=2, padx=5, pady=5)
        self.zaxis_cb.grid(column=0, row=5, padx=5, pady='2 5')
        self.zaxis_unit_cb.grid(column=1, row=5, padx='0 5', pady='2 5')

        self.dataclick_check.grid(column=0, row=6, columnspan=2, padx=5, pady=5)
        self.pt3Dshow_check.grid(column=0, row=7, columnspan=2, padx=5, pady=5)
        self.ptprojections_check.grid(column=0, row=8, columnspan=2, padx=5, pady=5)

        # Pack plot frame and options frame
        self.plot_frame.pack(side=LEFT, fill=BOTH, expand=YES)
        self.options_frame.pack(side=RIGHT, fill=BOTH, expand=1)

    def change_axis_var_event(self, event=None):
        self.xaxis_unit_cb['state'] = 'normal'
        self.yaxis_unit_cb['state'] = 'normal'
        self.zaxis_unit_cb['state'] = 'normal'
        self.xaxis_unit_cb['values'] = self.master.attr_dict[self.xaxis_var.get()]
        self.yaxis_unit_cb['values'] = self.master.attr_dict[self.yaxis_var.get()]
        self.zaxis_unit_cb['values'] = self.master.attr_dict[self.zaxis_var.get()]
        self.xaxis_unit_cb.current(0)
        self.yaxis_unit_cb.current(0)
        self.zaxis_unit_cb.current(0)
        self.xaxis_unit_cb['state'] = 'readonly'
        self.yaxis_unit_cb['state'] = 'readonly'
        self.zaxis_unit_cb['state'] = 'readonly'
        self.plot3d()

    def plot3d(self):
        # Use user-specified axis choices to retrieve real attribute names and units for that attribute
        xvar_attr_name = self.master.attr_names[self.master.attr_dict.keys().index(self.xaxis_var.get())]
        yvar_attr_name = self.master.attr_names[self.master.attr_dict.keys().index(self.yaxis_var.get())]
        zvar_attr_name = self.master.attr_names[self.master.attr_dict.keys().index(self.zaxis_var.get())]
        xvar_unit = self.xaxis_unit_var.get()
        yvar_unit = self.yaxis_unit_var.get()
        zvar_unit = self.zaxis_unit_var.get()

        # Create x, y, and z lists and loop through all feasible alternatives to populate the lists
        x = []
        y = []
        z = []
        c = []
        for alt in self.master.f_alts:
            xattr = getattr(alt, xvar_attr_name)
            yattr = getattr(alt, yvar_attr_name)
            zattr = getattr(alt, zvar_attr_name)
            x.append(convert_unit(xattr['value'], xattr['unit'], xvar_unit))
            y.append(convert_unit(yattr['value'], yattr['unit'], yvar_unit))
            z.append(convert_unit(zattr['value'], zattr['unit'], zvar_unit))
            if alt.pareto:
                c.append('r')
            else:
                c.append('b')

        self.ax3d.clear()
        if self.pt3Dshow_var.get():
            self.ax3d.scatter(x, y, z, c=c, picker=True)
        if self.ptprojections_var.get():
            self.ax3d.scatter(x, y, [0]*len(x), c=c, picker=True)
            self.ax3d.scatter(x, [0]*len(x), z, c=c, picker=True)
            self.ax3d.scatter([0]*len(y), y, z, c=c, picker=True)
        self.ax3d.set_xlabel(self.xaxis_var.get()+' ('+xvar_unit+')')
        self.ax3d.set_ylabel(self.yaxis_var.get()+' ('+yvar_unit+')')
        self.ax3d.set_zlabel(self.zaxis_var.get()+' ('+zvar_unit+')')
        self.ax3d.set_xlim([0, np.ceil(max(x)*1.2)])
        self.ax3d.set_ylim([0, np.ceil(max(y)*1.2)])
        self.ax3d.set_zlim([0, np.ceil(max(z)*1.2)])

        # When the user selects a point, display information about the datapoint (i.e., alternative) selected in a new
        # toplevel defined by the DisplayAlternative class. Because of something to do with Matplotlib, when a point is
        # selected in a canvas with multiple artists potentially overlapping, multiple identical events are thrown
        # during a pick. Therefore I am using a variable (self.last_pick_event) to hold the last unique pick event, only
        # processing a pick if it is different than self.last_pick_event.
        def pick_handler(event):
            if self.dataclick_var.get():
                if event is not self.last_pick_event:
                    self.last_pick_event = event
                    ind = event.ind
                    selected_alt = self.master.f_alts[ind[0]]
                    DisplayAlternative(self, selected_alt)
        self.canvas.mpl_connect('pick_event', pick_handler)
        self.canvas.show()


class VariableDistrPlot(ttk.Frame):
    def __init__(self, master):
        ttk.Frame.__init__(self, master, padding=5)
        self.master = master

        # Create plot and options frame
        self.plot_frame = ttk.Frame(self, padding=5)
        self.options_frame = ttk.Frame(self, padding=5)

        # Create options frame widgets
        self.attr2plot_label = ttk.Label(self.options_frame, text="Select quantity to plot.")

        self.attr2plot_var = StringVar()
        self.attr2plot_cb = ttk.Combobox(self.options_frame, textvariable=self.attr2plot_var,
                                         values=self.master.attr_dict.keys(), state='readonly')
        self.attr2plot_cb.current(0)
        self.attr2plot_cb.bind("<<ComboboxSelected>>", self.change_axis_var_event)

        self.attr2plot_unit_var = StringVar()
        self.attr2plot_unit_cb = ttk.Combobox(self.options_frame, textvariable=self.attr2plot_unit_var,
                                              values=self.master.attr_dict[self.attr2plot_var.get()], width=4,
                                              state='readonly')
        self.attr2plot_unit_cb.current(0)
        self.attr2plot_unit_cb.bind("<<ComboboxSelected>>", self.change_unit_event)

        self.dataclick_var = IntVar()
        self.dataclick_check = ttk.Checkbutton(self.options_frame, text="Activate selectable data points",
                                               variable=self.dataclick_var)

        # Create plot frame widgets
        self.fig = Figure(figsize=(6, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)

        self.ax.set_axisbelow(True)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)

        # Set up storage variable to hold the last pick event (see self.plot3d.pick_handler for details)
        self.last_pick_event = matplotlib.backend_bases.PickEvent

        # Call plot() for the first time
        self.plot()

        # Create the plot toolbar
        self.toolbar = NavigationToolbar2TkAgg(self.canvas, self.plot_frame)
        self.toolbar.update()
        self.canvas._tkcanvas.pack(side=TOP, fill=BOTH, expand=1)

        # Grid options frame widgets
        self.attr2plot_label.grid(column=0, row=0, columnspan=2, padx=5, pady=5)
        self.attr2plot_cb.grid(column=0, row=1, padx=5, pady='2 5')
        self.attr2plot_unit_cb.grid(column=1, row=1, padx='0 5', pady='2 5')
        self.dataclick_check.grid(column=0, row=2, columnspan=2, padx=5, pady=5)

        # Pack plot frame and options frame
        self.plot_frame.pack(side=LEFT, fill=BOTH, expand=YES)
        self.options_frame.pack(side=RIGHT, fill=BOTH, expand=1)

    def plot(self):
        attr_name = self.master.attr_names[self.master.attr_dict.keys().index(self.attr2plot_var.get())]
        attr_unit = self.attr2plot_unit_var.get()

        f_alts_sorted = sorted(self.master.f_alts, key=lambda x: getattr(x, attr_name)['value'])
        attr_vals = []
        num_alt_range = range(1, len(self.master.f_alts)+1)
        c = []
        for alt in f_alts_sorted:
            attr_val = getattr(alt, attr_name)
            attr_vals.append(convert_unit(attr_val['value'], attr_val['unit'], attr_unit))
            if alt.pareto:
                c.append('r')
            else:
                c.append('b')

        self.ax.clear()
        self.ax.scatter(num_alt_range, attr_vals, c=c, picker=True)
        self.ax.grid(True)
        self.ax.set_xlabel("All Feasible Alternatives")
        self.ax.set_ylabel(self.attr2plot_var.get()+' ('+attr_unit+')')
        self.ax.set_ylim([0, np.ceil(max(attr_vals))])
        self.ax.set_xlim([0, max(num_alt_range)+1])
        red_marker, = self.ax.plot(range(1), range(1), color='white', marker='o', markerfacecolor='red',
                                   label='Non-dominated alt')
        blue_marker, = self.ax.plot(range(1), range(1), color='white', marker='o', markerfacecolor='blue',
                                    label='Dominated alt')
        self.ax.legend(handles=[red_marker, blue_marker], numpoints=1, loc=4)

        # When the user selects a point, display information about the datapoint (i.e., alternative) selected in a new
        # toplevel defined by the DisplayAlternative class.
        def pick_handler(event):
            if self.dataclick_var.get():
                if event is not self.last_pick_event:
                    self.last_pick_event = event
                    ind = event.ind
                    selected_alt = self.master.f_alts[ind[0]]
                    DisplayAlternative(self, selected_alt)
        self.canvas.mpl_connect('pick_event', pick_handler)
        self.canvas.show()

    def change_axis_var_event(self, event=None):
        self.attr2plot_unit_cb['state'] = 'normal'
        self.attr2plot_unit_cb['values'] = self.master.attr_dict[self.attr2plot_var.get()]
        self.attr2plot_unit_cb.current(0)
        self.attr2plot_unit_cb['state'] = 'readonly'
        self.plot()

    def change_unit_event(self, event=None):
        self.plot()


class DisplayAlternative(Toplevel):
    def __init__(self, master, alt):
        Toplevel.__init__(self, master)
        self.master = master
        self.alt = alt
        xpos, ypos = get_win_place(self)
        self.geometry('+%d+%d' % (xpos, ypos))
        self.title(str(alt))

        self.mainframe = ttk.Frame(self)
        self.mainframe.pack(fill=BOTH, expand=YES)

        self.comp_frame_label = ttk.Label(self.mainframe, text='General Info')
        self.perf_frame_label = ttk.Label(self.mainframe, text='Performance')

        self.alt_comp_frame = alt.display_frame(self.mainframe, header=True, mode='regular')
        self.alt_perf_frame = alt.display_frame(self.mainframe, header=True, mode='perf')

        self.comp_frame_label.pack(pady='10')
        self.alt_comp_frame.pack(fill=X, expand=1, pady='5 10', padx=5)
        self.perf_frame_label.pack(pady='10')
        self.alt_perf_frame.pack(fill=X, expand=1, pady='5 10', padx=5)


