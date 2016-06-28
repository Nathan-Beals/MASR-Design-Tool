"""
Created on Sat Feb 27 11:20:47 2016
author: Zachary Fisher
Modified by: Devan Thanki
"""
import os
import win32com.client
import pythoncom
import datetime

from masr_design_tool.tools import convert_unit
from matplotlib.mlab import quad2cubic


def build_model(quad,cover_flag):
    # Initialize an instance of SolidWorks 201X
    # swYearLastDigit = 4
    # This will fetch the existing version of Solidworks present on the system
    swApp = win32com.client.Dispatch("SldWorks.Application")
    
    # Open the multirotor model
    modelPath = os.path.abspath(os.path.join(os.path.dirname(__file__), 'model/', 'Quad_Assembly.SLDASM'))
    longstatus = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, -1)
    longwarnings = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, -1)
    swApp.OpenDoc6(modelPath, 2, 0, "", longstatus, longwarnings)
    
    # Make the model the active model
    swApp.ActivateDoc2("Quad_Assembly.SLDASM", False, longstatus)
    model = swApp.ActiveDoc
    
    # Assign any manager objects that will be needed
    # modelExt = model.Extension
    # selMgr = model.SelectionManager
    # featureMgr = model.FeatureManager
    # sketchMgr = model.SketchManager
    eqMgr = model.GetEquationMgr
    
    # Change the dimension parameters in the equation editor
#     hub_separation = convert_unit(quad.hub_separation['value'], 'm', 'in')    
#     hub_size = convert_unit(quad.hub_size['value'], 'm', 'in') 
#     hub_corner_len = convert_unit(quad.hub_corner_len['value'], 'm', 'in') 
#     arm_len = convert_unit(quad.arm_len['value'], 'm', 'in') 
#     eqMgr.Equation(0, "\"Number_Arms\" = " + str(int(quad.n_arms['value'])))
#     eqMgr.Equation(1, "\"Hub_LayerSeparation_1_2\" = " + str(hub_separation))
#     eqMgr.Equation(2, "\"Hub_Width\" = " + str(hub_size))
#     eqMgr.Equation(3, "\"Arm_Base_Width\" = " + str(hub_corner_len))
#     eqMgr.Equation(5, "\"Arm_Length\" = " + str(arm_len))

    prop_dia = convert_unit(quad.prop.diameter['value'], 'm', 'in')
    plate_xdim = 4.25 # inches
    plate_ydim = 5.75 # inches
    plate_thickness = 0.1 #inches
    bat_xdim = convert_unit(quad.battery.xdim['value'], 'm', 'in')
    bat_ydim = convert_unit(quad.battery.ydim['value'], 'm', 'in')
    bat_zdim = convert_unit(quad.battery.zdim['value'], 'm', 'in')
    #arm_length = convert_unit(quad.arm_len['value'], 'm', 'in')
    arm_len = prop_dia *0.357 + 2.965 # in inches, according to Solidworks equation manager
    # esc_xdim = 
    # esc_ydim = 
    # esc_zdim = 
    comp_y = 1.64 # inches
    dowell_height = 0.1 #inches
    dowell_width = 0.25 #inches
    # motor_screw_ydim = 
    # motor_screw_xdim = 
    gimbal_mount = 0
    payload_bot_z = 0
    # motor_screw_dia
    gps_x = 2 # inches
    gps_y = 2 # inches
    gps_z = 0.5 # inches
    flight_controller_xdim = 3 # inches
    flight_controller_ydim = 2.25 # inches
    flight_controller_zdim = 0.5 # inches
    radio_rx_xdim = 1.13 # inches
    radio_rx_xdim = 2 # inches
    radio_rx_xdim = 0.5 # inches
    cover = cover_flag
    motor_dia = convert_unit(quad.motor.body_diameter['value'], 'm', 'in')
    # motor_len =
    # motor_shaft_dia =  
    
    eqMgr.Equation(0, "\"Propeller Size\" = " + str(prop_dia)+ "in")
    eqMgr.Equation(1, "\"Plate Dim X\" = " + str(plate_xdim)+ "in")
    eqMgr.Equation(2, "\"Plate Dim Y\" = " + str(plate_ydim)+ "in")
    eqMgr.Equation(3, "\"Plate Thickness\" = " + str(plate_thickness)+ "in")
    eqMgr.Equation(4, "\"Batt X\" = " + str(bat_xdim)+ "in")
    eqMgr.Equation(5, "\"Batt Y\" = " + str(bat_ydim)+ "in")
    eqMgr.Equation(6, "\"Batt Z\" = " + str(bat_zdim)+ "in")
    eqMgr.Equation(7, "\"Arm Length\" = " + str(arm_len)+ "in")
    eqMgr.Equation(8, "\"ESC Y\" = " + str(2.4)+ "in") # temp value
    eqMgr.Equation(9, "\"ESC X\" = " + str(26) + "mm") # temp value
    eqMgr.Equation(10, "\"ESC Z\" = " + str(10.5) + "mm") # temp value
    eqMgr.Equation(11, "\"Component Y\" = " + str(1.64)+ "in")
    eqMgr.Equation(12, "\"Dowell Height\" = " + str(0.1)+ "in")
    eqMgr.Equation(13, "\"Dowell Width\" = " + str(0.25)+ "in")
    eqMgr.Equation(14, "\"Motor Screw Y\" = " + str(25)+ "mm")
    eqMgr.Equation(15, "\"Motor Screw X\" = " + str(19)+ "mm")
    eqMgr.Equation(16, "\"Gimbal Mount\" = " + str(0))
    eqMgr.Equation(17, "\"Payload Bot Z\" = " + str(0))
    eqMgr.Equation(18, "\"Motor Screw Diam\" = " + str(3)+ "mm")
    eqMgr.Equation(19, "\"GPS X\" = " + str(2)+ "in")
    eqMgr.Equation(20, "\"GPS y\" = " + str(2)+ "in")
    eqMgr.Equation(21, "\"GPS Z\" = " + str(0.5)+ "in")
    eqMgr.Equation(22, "\"Flight Controller X\" = " + str(2)+ "in")
    eqMgr.Equation(23, "\"Flight Controller Y\" = " + str(3.25)+ "in")
    eqMgr.Equation(24, "\"Flight Controller Z\" = " + str(0.5)+ "in")
    eqMgr.Equation(25, "\"Radio Rx X\" = " + str(1.13)+ "in")
    eqMgr.Equation(26, "\"Radio Rx Y\" = " + str(2)+ "in")
    eqMgr.Equation(27, "\"Radio Rx Z\" = " + str(0.5)+ "in")
    eqMgr.Equation(28, "\"Cover\" = " + str(cover))
    eqMgr.Equation(29, "\"Motor Diam\" = " + str(motor_dia)+ "in")
    eqMgr.Equation(30, "\"Motor Length\" = " + str(23)+ "mm")
    eqMgr.Equation(31, "\"Motor Shaft Diam\" = " + str(3)+ "mm")
    # Rebuild the model so the new parameters take effect
    boolstatus = model.EditRebuild3
    
    # Save off a folder of .STL files of the new parts
    now = datetime.datetime.now()
    ModelDataDir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'modelOutput/' +
                                                now.strftime("%Y-%m-%d_%H%M")))
    if not os.path.exists(ModelDataDir):
        os.makedirs(ModelDataDir)
    
    # Toggle the "save as single STL" preference off
    arg1 = win32com.client.VARIANT(pythoncom.VT_I4, 72)
    argBool = win32com.client.VARIANT(pythoncom.VT_BOOL, False)
    swApp.SetUserPreferenceToggle(arg1, argBool)
    # Save individual .STL files
    longstatus = model.SaveAs3(ModelDataDir + "\Multirotor.STL", 0, 0)
    # Toggle the "save as single STL" preference on
    argBool = win32com.client.VARIANT(pythoncom.VT_BOOL, True)
    swApp.SetUserPreferenceToggle(arg1, argBool)
    #swApp.SetUserPreferenceToggle swUserPreferenceToggle_e.swSTLCheckForInterference, True
    # Save a single .STL of the whole model for viewing purposes
    longstatus = model.SaveAs3(ModelDataDir + "\Multirotor.STL", 0, 0)
    # Toggle the "save as single STL" preference back off    
    argBool = win32com.client.VARIANT(pythoncom.VT_BOOL, False)
    swApp.SetUserPreferenceToggle(arg1, argBool)
    
    # Close the model
    model = None
    #swApp.CloseDoc("Multirotor.SLDASM")
    #swApp.ExitApp()
    
#     from stl import mesh
#     from mpl_toolkits import mplot3d
#     from matplotlib import pyplot
#     
#     # Create a new plot
#     figure = pyplot.figure()
#     axes = mplot3d.Axes3D(figure)
#     
#     # Load the STL files and add the vectors to the plot
#     vehicle_mesh = mesh.Mesh.from_file(ModelDataDir + '/Multirotor.STL')
#     axes.add_collection3d(mplot3d.art3d.Poly3DCollection(vehicle_mesh.vectors))
#     
#     # Auto scale to the mesh size
#     scale = vehicle_mesh.points.flatten(-1)
#     axes.auto_scale_xyz(scale, scale, scale)
#     
#     # Show the plot to the screen
#     pyplot.show()