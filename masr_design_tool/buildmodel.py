"""
Created on Sat Feb 27 11:20:47 2016
author: Zachary Fisher
Modified by: Devan Thanki
"""
import os
import shutil
import datetime


from tools import convert_unit
#from matplotlib.mlab import quad2cubic



def build_model(quad,cover_flag, alt_infovar):
    try:
        import win32com.client
    except ImportError:
        alt_infovar.set("win32com.client module not installed for export.")
        return

    try:
        import pythoncom
    except ImportError:
        alt_infovar.set("pythoncom module not installed for export.")
        return

    # Initialize an instance of SolidWorks 201X
    # swYearLastDigit = 4
    # sw = win32com.client.Dispatch("SldWorks.Application.%d" % (20+(swYearLastDigit-2)))
    # If more than one version is installed, activate the two lines of code preceding this comment
    # This will fetch the existing version of Solidworks present on the system, if only single version is present

     # Save a new folder
    now = datetime.datetime.now()
    ModelDataDir = os.path.join(os.path.dirname(__file__), 'modelOutput' +
                                now.strftime("%Y-%m-%d_%H%M%S"))
    if not os.path.exists(ModelDataDir):
        os.makedirs(ModelDataDir)

    model_path = os.path.join(os.path.dirname(__file__), 'model')

    for file_name in os.listdir(model_path):
            full_file_name = os.path.join(model_path, file_name)
            shutil.copy(full_file_name, ModelDataDir)

    swApp = win32com.client.Dispatch("SldWorks.Application")
    swApp.Visible = True

    # Open the multirotor model
    modelPath = os.path.abspath(os.path.join(ModelDataDir, 'Quad Assemb.SLDASM'))
    longstatus = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, -1)
    longwarnings = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, -1)
    swApp.OpenDoc6(modelPath, 2, 0, "", longstatus, longwarnings)

    # Make the model the active model
    swApp.ActivateDoc2("Quad Assemb.SLDASM", False, longstatus)
    model = swApp.ActiveDoc
    eqMgr = model.GetEquationMgr


    prop_dia = convert_unit(quad.prop.diameter['value'], 'm', 'in')
    plate_xdim = 4.25 # inches
    plate_ydim = 5.75 # inches
    plate_thickness = 0.1 #inches
    bat_xdim = convert_unit(quad.battery.ydim['value'], 'm', 'in') #X and Y dimensions are interchanged
    bat_ydim = convert_unit(quad.battery.xdim['value'], 'm', 'in')
    bat_zdim = convert_unit(quad.battery.zdim['value'], 'm', 'in')
    arm_length = convert_unit(quad.arm_len['value'], 'm', 'in')
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

    #Change the hard link to the external equations text file
    eqMgr.FilePath =os.path.abspath(os.path.join(ModelDataDir, 'equations.txt'))

    file = open(os.path.abspath(os.path.join(ModelDataDir, 'equations.txt')),'w')

    file.write( "\"Propeller Size\"= " + str(prop_dia) + "in" + '\n')
    file.write( "\"Plate Dim X\"= " + str(plate_xdim)+ "in" + '\n')
    file.write( "\"Plate Dim Y\"= " + str(plate_ydim)+ "in" + '\n')
    file.write( "\"D2@Sketch1\"=\"Propeller Size\"" + '\n')
    file.write( "\"Plate Thickness\"= " + str(plate_thickness)+ "in" + '\n')
    file.write( "\"Batt X\"= " + str(bat_xdim)+ "in" + '\n')
    file.write( "\"Batt Y\"= " + str(bat_ydim)+ "in" + '\n')
    file.write( "\"Batt Z\"= " + str(bat_zdim)+ "in" + '\n')
    file.write( "\"Arm Length\"= \"Propeller Size\" * .357 + 2.965" + '\n')
    file.write( "\"ESC Y\"= " + str(2.4)+ "in" + '\n') # temp value
    file.write( "\"ESC X\"= " + str(26) + "mm" + '\n') # temp value
    file.write( "\"ESC Z\"= " + str(10.5) + "mm" + '\n') # temp value
    file.write( "\"Component Y\"= " + str(1.64)+ "in" + '\n')
    file.write( "\"Dowell Height\"= " + str(0.1) + '\n')
    file.write( "\"Dowell Width\"= " + str(0.25) + '\n')
    file.write( "\"Motor Screw Y\"= " + str(25)+ "mm" + '\n')
    file.write( "\"Motor Screw X\"= " + str(19)+ "mm" + '\n')
    file.write( "\"Gimbal Mount\"= " + str(0)+ '\n')
    file.write( "\"Payload Bot Z\"= " + str(0)+ '\n')
    file.write( "\"Motor Screw Diam\"= " + str(3)+ "mm" + '\n')
    file.write( "\"GPS X\"= " + str(2) + '\n')
    file.write( "\"GPS Y\"= " + str(2) + '\n')
    file.write( "\"GPS Z\"= " + str(0.5) + '\n')
    file.write( "\"Flight Controller X\"= " + str(2) + '\n')
    file.write( "\"Flight Controller Y\"= " + str(3.25) + '\n')
    file.write( "\"Flight Controller Z\"= " + str(0.5) + '\n')
    file.write( "\"Radio Rx X\"= " + str(1.13) + '\n')
    file.write( "\"Radio Rx Y\"= " + str(2) + '\n')
    file.write( "\"Radio Rx Z\"= " + str(0.5) + '\n')
    file.write( "\"D1@Sketch1\"=\"Propeller Size\"/2+4" + '\n')
    file.write( "\"Cover\"= " + str(cover) + '\n')
    file.write( "\"Top Plate-1.Part\"= if ( \"Cover\" = 0 , \"unsuppressed\" , \"suppressed\" )" + '\n')
    file.write( "\"Top Plate Cover_new-1.Part\"= if ( \"Cover\" = 1 , \"unsuppressed\" , \"suppressed\" )" + '\n')
    file.write( "\"Motor Diam\"= " + str(motor_dia)+ "in" + '\n')
    file.write( "\"Motor Length\"= " + str(23)+ "mm" + '\n')
    file.write( "\"Motor Shaft Diam\"= " + str(3)+ "mm" + '\n')
    file.close()
    boolstatus = model.EditRebuild3

    # Save a single .SLDASM of the whole model for viewing purposes
    longstatus = model.SaveAs3(modelPath, 0, 0)

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
    # swApp.CloseDoc("Quad Assemb.SLDASM")
    # swApp.ExitApp()
    alt_infovar.set("Model Built!")