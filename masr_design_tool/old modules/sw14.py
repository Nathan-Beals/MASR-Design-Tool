"""
Created on Sat Feb 27 11:20:47 2016
author: Zachary Fisher
"""
import os
import win32com.client
import pythoncom
import datetime

from masr_design_tool.tools import convert_unit


def build_model(quad):
    # Initialize an instance of SolidWorks 201X
    swYearLastDigit = 4
    swApp = win32com.client.Dispatch("SldWorks.Application.%d" % (20+(swYearLastDigit-2)))
    
    # Open the multirotor model
    modelPath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'Multirotor.SLDASM'))
    longstatus = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, -1)
    longwarnings = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, -1)
    swApp.OpenDoc6(modelPath, 2, 0, "", longstatus, longwarnings)
    
    # Make the model the active model
    swApp.ActivateDoc2("Multirotor.SLDASM", False, longstatus)
    model = swApp.ActiveDoc
    
    # Assign any manager objects that will be needed
    # modelExt = model.Extension
    # selMgr = model.SelectionManager
    # featureMgr = model.FeatureManager
    # sketchMgr = model.SketchManager
    eqMgr = model.GetEquationMgr
    
    # Change the dimension parameters in the equation editor
    hub_separation = convert_unit(quad.hub_separation['value'], 'm', 'in')    
    hub_size = convert_unit(quad.hub_size['value'], 'm', 'in') 
    hub_corner_len = convert_unit(quad.hub_corner_len['value'], 'm', 'in') 
    arm_len = convert_unit(quad.arm_len['value'], 'm', 'in') 
    eqMgr.Equation(0, "\"Number_Arms\" = " + str(int(quad.n_arms['value'])))
    eqMgr.Equation(1, "\"Hub_LayerSeparation_1_2\" = " + str(hub_separation))
    eqMgr.Equation(2, "\"Hub_Width\" = " + str(hub_size))
    eqMgr.Equation(3, "\"Arm_Base_Width\" = " + str(hub_corner_len))
    eqMgr.Equation(5, "\"Arm_Length\" = " + str(arm_len))
    
    # Rebuild the model so the new parameters take effect
    boolstatus = model.EditRebuild3
    
    # Save off a folder of .STL files of the new parts
    now = datetime.datetime.now()
    ModelDataDir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models/' +
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
    
    from stl import mesh
    from mpl_toolkits import mplot3d
    from matplotlib import pyplot
    
    # Create a new plot
    figure = pyplot.figure()
    axes = mplot3d.Axes3D(figure)
    
    # Load the STL files and add the vectors to the plot
    vehicle_mesh = mesh.Mesh.from_file(ModelDataDir + '/Multirotor.STL')
    axes.add_collection3d(mplot3d.art3d.Poly3DCollection(vehicle_mesh.vectors))
    
    # Auto scale to the mesh size
    scale = vehicle_mesh.points.flatten(-1)
    axes.auto_scale_xyz(scale, scale, scale)
    
    # Show the plot to the screen
    pyplot.show()