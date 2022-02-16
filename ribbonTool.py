''' Ribbon Tool v1.2 '''

import maya.cmds as cmds
import maya.mel as mm

class ribbonMaker:
    def run(self):
        ''' Runs the ribbon UI function when the script is called '''
        self.ribbonUI()
        
             
    def createRibbon(self, *args):
        ''' 
        Main function for creating the ribbon. 
        Sets variables and runs other functions in order
        '''
        nurbsName = cmds.textField("nameMenu", q=1, tx=1)
        nurbsLength = cmds.floatField("lengthMenu", q=1, v=1)
        nurbsDirection = cmds.optionMenu("directionMenu", q=1, v=1)
        nurbsAxis = cmds.optionMenu("axisMenu", q=1, v=1)
        jointAxis = cmds.optionMenu("jointAxisMenu", q=1, v=1)
        jointInvert = cmds.checkBox("snapInvertCheck", q=1, v=1)
        insertIsoparm = cmds.checkBox("isoparmCheck", q=1, v=1)
        ctrlScale = cmds.floatField("scaleMenu", q=1, v=1)
        ctrlColour = cmds.colorSliderGrp("colourMenu", q=1, rgb=1)
        jointSnap = cmds.checkBox("snapCheck", q=1, v=1)
        endOrient = cmds.checkBox("endJointCheck", q=1, v=1)
        
        # Creates an empty list to be populated with the joint heirarchy to snap to
        jointHeirarchy = []
        if jointSnap:
            jointHeirarchy = self.snapHeirarchy()
            
        # Sets plane axis value for the nurbs surface based on the chosen facing axis
        if nurbsAxis == "X":
            planeAxis = [1, 0, 0]
        elif nurbsAxis == "Y":
            planeAxis = [0, 1 ,0]
        else:
            planeAxis = [0, 0, 1]
                    
        # Sets joint orient values to rotate the created joints to match the joing chain axis
        if not jointInvert:
            if jointAxis == "X":
                jointOrient = [-90, 0, 0]
            elif jointAxis == "Y":
                jointOrient = [0, 180, -90]
            else:
                jointOrient = [0, 90, 0]
        else:
            if jointAxis == "X":
                jointOrient = [-90, -180, 0]
            elif jointAxis == "Y":
                jointOrient = [0, 0, 90]
            else:
                jointOrient = [0, -90, 0]    
        endJointOrient = [0, 0, 0]
        if not endOrient:
            endJointOrient = jointOrient
        
        # Checks for no ribbon name and already existing ribbon names                    
        if nurbsName == "":
            cmds.error("Please enter a ribbon name")
        if cmds.objExists(nurbsName):
            cmds.error("A ribbon with that name already exists, please select a unique name")
    
        jointCount = 3
        nurbsDivisions = 8
        ribbonName = nurbsName + "_ribbon"
        ribbonWidth = nurbsLength / 5
        
        # Creates ribbon, rotates if needed and inserts isoparms
        cmds.nurbsPlane(ax=planeAxis, d=3, lr=0.15, u=nurbsDivisions, v=1, w=nurbsLength, n=ribbonName)
        if nurbsDirection == "Vertical":
            cmds.setAttr(ribbonName+".rotate"+nurbsAxis, -90)
            cmds.makeIdentity(ribbonName, apply=True, rotate=True)
        if insertIsoparm:
            cmds.insertKnotSurface((ribbonName+'.u[0.490]'), ch=True, nk=1, rpo=1)
            cmds.insertKnotSurface((ribbonName+'.u[0.510]'), ch=True, nk=1, rpo=1)
        cmds.select(cl=1)    
        
        # Runs functions to set up the ribbon further
        self.addDeformers(nurbsName, ribbonName, nurbsDirection)
        ribbonJnt, ribbonBindList = self.addFollicles(nurbsName, ribbonName, nurbsDivisions, nurbsDirection, jointOrient, endJointOrient)
        snapCtrl = self.addControllers(ribbonWidth, ribbonJnt, ribbonBindList, nurbsName)
        if jointSnap:
            self.snapControl(snapCtrl, jointHeirarchy)
        self.cleanHeirarchy(nurbsName)
        self.connectDeformers(nurbsName, nurbsDirection)
        self.aimAndPoint(nurbsName, jointAxis, jointInvert)
                
        
    def aimAndPoint(self, name, jointAxis, invert):     # Aim and point constraints
        ''' Create aim and point constraints for controllers between base, mid and end '''
        ribbonBase = f"{name}_base"
        ribbonMid = f"{name}_mid"
        ribbonEnd = f"{name}_end"
        
        # Set variable values based on the main axis and sign of the joint chain and ribbon joints
        # Ensures constraints are oriented correclty and aren't flipped
        if not invert:
            if jointAxis == "X":
                upperAimVect = (1, 0, 0)
                lowerAimVect = (-1, 0, 0)
                controlUp = (0, 1, 0)
            elif jointAxis == "Y":
                upperAimVect = (0, 1, 0)
                lowerAimVect = (0, -1, 0)
                controlUp = (0, 0, 1)                
            elif jointAxis == "Z":
                upperAimVect = (0, 0, 1)
                lowerAimVect = (0, 0, -1)
                controlUp = (1, 0, 0)                
        else:
            if jointAxis == "X":
                upperAimVect = (-1, 0, 0)
                lowerAimVect = (1, 0, 0)
                controlUp = (0, 1, 0)                
            elif jointAxis == "Y":
                upperAimVect = (0, -1, 0)
                lowerAimVect = (0, 1, 0)
                controlUp = (0, 0, 1)                
            elif jointAxis == "Z":
                upperAimVect = (0, 0, -1)
                lowerAimVect = (0, 0, 1)
                controlUp = (1, 0, 0)  
                              
        # Create and place upper and lower aimpoint groups
        upAPGrp = cmds.group(n=f"{name}"+"_upper_aimpoint", em=1)
        lowAPGrp = cmds.group(n=f"{name}"+"_lower_aimpoint", em=1)        
        cmds.parent(upAPGrp, ribbonBase+"_jnt")
        cmds.matchTransform(upAPGrp, ribbonBase+"_jnt")    
        cmds.parent(lowAPGrp, ribbonMid+"_jnt")
        cmds.matchTransform(lowAPGrp, ribbonMid+"_jnt") 
        # Create point constraints
        cmds.pointConstraint(ribbonBase+"_jnt", ribbonMid+"_jnt", f"{name}"+"_upper_grp", w=1)
        cmds.pointConstraint(ribbonEnd+"_jnt", ribbonMid+"_jnt", f"{name}"+"_lower_grp", w=1)
        # Create aim constraints       
        cmds.aimConstraint(ribbonMid+"_jnt", f"{name}"+"_upper_aim", aim=upperAimVect, u=controlUp, wu=controlUp, wut="objectrotation", wuo=upAPGrp, w=1)
        cmds.aimConstraint(ribbonMid+"_jnt", f"{name}"+"_lower_aim", aim=lowerAimVect, u=controlUp, wu=controlUp, wut="objectrotation", wuo=lowAPGrp, w=1)
        cmds.select(cl=1)
        
        
    def cleanHeirarchy(self, name):  
        ''' Organises and cleans up the heirarchy '''
        cmds.parent(f"{name}"+"_follicles", f"{name}"+"_deform")
        masterGrp = cmds.group(n=f"{name}"+"_ribbon_grp", em=1)
        cmds.parent(f"{name}"+"_deform", f"{name}"+"_offset_grp", masterGrp)
        cmds.select(cl=1)
        
        
    def addControllers(self, width, jointList, ribbonBindList, name):
        ''' Creates controllers and control joints so the ribbon can be deformed '''
        jointAxis = cmds.optionMenu("jointAxisMenu", q=1, v=1)        
        ctrlScale = cmds.floatField("scaleMenu", q=1, v=1)
        mainCtrlColour = cmds.colorSliderGrp("colourMenu", q=1, rgb=1)
        altCtrlColour = cmds.colorSliderGrp("altColourMenu", q=1, rgb=1)
        altColourCheck = cmds.checkBox("altColourCheck", q=1, v=1)
        ctrlList = []
        snapCtrl = []
        
        # Sets normal axis direction for circle creation
        if jointAxis == "X":
            normal = (1, 0, 0)
        elif jointAxis == "Y":
            normal = (0, 1, 0)
        elif jointAxis == "Z":
            normal = (0, 0, 1)
        
        mainScale = ((width/1.4)*ctrlScale)
        smallScale = ((width/1.7)*ctrlScale)     
        
        # Loop with a range of 5 to create a controller at every other ribbon joint
        for c, value in enumerate(jointList):
            # If on an even loop (upper / lower joints) make circle with certain radius, and group
            if c % 2:
                controller = cmds.circle(n=value+"_ctrl", nr=normal, r=smallScale)
            else:
                controller = cmds.circle(n=value+"_ctrl", nr=normal, r=mainScale)
            ctrlGrp = cmds.group(controller, n=value+"_ctrl_grp")
            # Place in aditional buffer group if upper or lower joint
            if c % 2:
                aimGrp = cmds.group(ctrlGrp, n=value+"_aim")
                parentGrp = cmds.group(aimGrp, n=value+"_grp")
            else:
                parentGrp = cmds.group(ctrlGrp, n=value+"_grp")
            offsetGrp = cmds.group(parentGrp, n=value+"_offset")
            # Place offset in same place as ribbon joint and parent the control joint
            cmds.matchTransform(offsetGrp, value+"_jnt")
            cmds.parent(value+"_jnt", controller[0])
            # Set controller colour
            cmds.setAttr(controller[0]+"Shape.overrideEnabled", 1)
            cmds.setAttr(controller[0]+"Shape.overrideRGBColors", 1)
            if c % 2 and altColourCheck:
                cmds.setAttr(controller[0]+"Shape.overrideColorRGB", type="float3", *altCtrlColour)
            else:
                cmds.setAttr(controller[0]+"Shape.overrideColorRGB", type="float3", *mainCtrlColour)
            snapCtrl.append(value+"_offset")
            ctrlList.append(offsetGrp)
            cmds.select(cl=1)
        
        # Group control offset groups and skin ribbon to bind joints
        ctrlGrp = cmds.group(n=f"{name}"+"_offset_grp", em=1)
        cmds.parent(ctrlList, ctrlGrp)
        cmds.select(ribbonBindList)
        cmds.skinCluster(mi=2, tsb=True)
        cmds.select(cl=1)
        return snapCtrl
        
        
    def snapControl(self, snapCtrl, snapJoints):
        ''' Snaps controller offset groups to joint chain and parents them '''
        for c, value in enumerate(snapCtrl):
            cmds.matchTransform((snapCtrl[c]), (snapJoints[c]), pos=1, rot=1)
            cmds.parentConstraint((snapJoints[c]), (snapCtrl[c]), mo=0)    
        cmds.select(cl=1)
    
    
    def addFollicles(self, name, ribbon, divisions, direction, jointOrient, endJointOrient):
        ''' Creates follicles and joints for the ribbon '''
        follicleCheck = cmds.checkBox("follicleCheck", q=1, v=1)
        follicleName = name + "_follicle"   
        
        # Creates follicles and deletes unneccessary components
        cmds.select (ribbon)
        mm.eval(f'createHair {divisions+1} 1 10 0 0 1 0 5 0 1 2 1;')  
        hairDelete = cmds.ls(f'hairSystem?', 'pfxHair?', 'nucleus?')
        cmds.delete(hairDelete)
        cmds.select("hairSystem?Follicles")
        cmds.rename(follicleName+"s")
        folliclesOldList = cmds.ls(f"{ribbon}"+"Follicle*", type="transform")

        # Renames follicles, deletes curve node and sets follicle visibility
        for i in range(len(folliclesOldList)):
            if follicleCheck:
                cmds.setAttr(folliclesOldList[i]+".visibility", 0)
            folliclesNewName = follicleName+"_00"
            cmds.select(folliclesOldList[i])
            cmds.rename(folliclesNewName)
            follicleCurves= cmds.ls("curve*")
            if follicleCurves:
                cmds.delete(follicleCurves)
        cmds.select(cl=1)
        
        visCheck = cmds.checkBox("visCheck", q=1, v=1)
        follicleCount = cmds.ls(f"{name}_follicle_??")
        ribbonBase = f"{name}_base"
        ribbonUpper = f"{name}_upper"
        ribbonMid = f"{name}_mid"
        ribbonLower = f"{name}_lower"
        ribbonEnd = f"{name}_end"
        ribbonJnt = [ribbonBase, ribbonUpper, ribbonMid, ribbonLower, ribbonEnd]
        ribbonJntList = [ribbonBase, 0, ribbonUpper, 0, ribbonMid, 0, ribbonLower, 0, ribbonEnd]
        ribbonBindList = []
        
        # Loop 9 times to create a joint at each follicle point
        for c, (value1, value2) in enumerate(zip(follicleCount, ribbonJntList)):
            bindJoint = cmds.joint(n=f"{name}_bind_{c:02}", rad=0.25)            
            if visCheck:
                cmds.setAttr(bindJoint+".visibility", 0)
            # If on an odd number make a duplicate joint, match transforms of follicle and add to list
            if c % 2 == 0 :
                cmds.duplicate(bindJoint, n=value2+"_jnt")
                cmds.setAttr(value2+"_jnt.radius", 0.4)
                cmds.matchTransform(value2+"_jnt", value1)
                # Orient to world is selected from UI
                if c == 0:
                    cmds.rotate((endJointOrient[0]), (endJointOrient[1]), (endJointOrient[2]), value2+"_jnt", r=1, os=1, fo=1)
                else:
                    cmds.rotate((jointOrient[0]), (jointOrient[1]), (jointOrient[2]), value2+"_jnt", r=1, os=1, fo=1)
                cmds.makeIdentity(value2+"_jnt", a=True, t=1, r=1, s=1, n=0, pn=1)
                ribbonBindList.append(value2+"_jnt")
            # Place bind joint under follicle
            cmds.parent(bindJoint, value1)
            cmds.matchTransform(bindJoint, value1)
            # Orient to world is selected from UI
            if c == 0:
                cmds.rotate((endJointOrient[0]), (endJointOrient[1]), (endJointOrient[2]), bindJoint, r=1, os=1, fo=1)
            else:
                cmds.rotate((jointOrient[0]), (jointOrient[1]), (jointOrient[2]), bindJoint, r=1, os=1, fo=1)
            cmds.makeIdentity(bindJoint, a=True, t=1, r=1, s=1, n=0, pn=1)
            cmds.select(cl=1)    
        cmds.select(cl=1)
        ribbonBindList.append(ribbon)
        
        return ribbonJnt, ribbonBindList
        
    
    def addDeformers(self, name, ribbon, direction):
        ''' Duplicate ribbon to make sine and twist blend shapes '''
        ribbonTwist = name+"_twist"
        ribbonSine = name+"_sine"
        twistDef = name+"_twist_def"
        sineDef = name+"_sine_def"
        twistHandle = name+"_twist_handle"
        sineHandle = name+"_sine_handle"
        bShape = name+"_bShape"
        
        cmds.duplicate(ribbon, n=ribbonTwist)
        cmds.duplicate(ribbon, n=ribbonSine)
        # Add sine and twist deformers, rotate if needed and create blend shape
        twist = cmds.nonLinear(ribbonTwist, type="twist")  
        sine = cmds.nonLinear(ribbonSine, type="sine") 
        if direction == "Horizontal":
            cmds.rotate(0, 0, 90, (sine[1]), (twist[1]), r=1, os=1)
        cmds.rename(sine[0], sineDef)
        cmds.rename(twist[0], twistDef)
        cmds.rename(sine[1], sineHandle)
        cmds.rename(twist[1], twistHandle)
        cmds.blendShape(ribbonSine, ribbonTwist, ribbon, n=bShape, foc=1)      
        cmds.setAttr((twistHandle+".visibility"), 0)
        cmds.setAttr((sineHandle+".visibility"), 0)
        cmds.setAttr(ribbonTwist+".visibility", 0)
        cmds.setAttr(ribbonSine+".visibility", 0)
        
        # Group deformer handles and ribbons along with the main ribbon
        ribbonGrp = cmds.group(n=f"{name}"+"_deform", em=1)
        cmds.parent(twistHandle, sineHandle, ribbonSine, ribbonTwist, ribbon, ribbonGrp)     
        cmds.select(cl=1)
        
        
    def connectDeformers(self, name, direction):   
        ''' Connect attributes to control twist and sine blend shapes '''
        baseCtrl = f"{name}"+"_base_ctrl"
        sineEnumAttr = f".{name}"+"SineDeform"
        twistEnumAttr = f".{name}"+"TwistDeform"
        ribbonTwist = name+"_twist"
        ribbonSine = name+"_sine"
        sineHandle = name+"_sine_handle"
        twistHandle = name+"_twist_handle"
        upCtrl = name+"_upper_ctrl"
        lowCtrl = name+"_lower_ctrl"
        
        # Asign correct axis to be connected depending on ribbon direction
        if direction == "Horizontal":
            transAxis = ".translateX"
        else:
            transAxis = ".translateY"
        
        # Add attributes to the base controller
        cmds.select(baseCtrl)
        cmds.addAttr(ln=f"{name}"+"SineDeform", at="enum", en="---------------", k=1)
        cmds.setAttr(baseCtrl+sineEnumAttr, l=1)
        cmds.addAttr(ln="SineBlend", at="float", min=0, max=1, k=1)
        cmds.addAttr(ln="SineAmplitude", at="float", dv=0.3, k=1)
        cmds.addAttr(ln="SineWavelength", at="float", dv=2.0, k=1)
        cmds.addAttr(ln="SineOrientation", at="float", k=1)
        cmds.addAttr(ln="SineAnimate", at="float", k=1)
        cmds.addAttr(ln="SineOffset", at="float", k=1)
        cmds.addAttr(ln="SineDropoff", at="float", min=0, max=1, dv=1.0, k=1)
        cmds.addAttr(ln=f"{name}"+"TwistDeform", at="enum", en="---------------", k=1)
        cmds.setAttr(baseCtrl+twistEnumAttr, l=1)
        cmds.addAttr(ln="TwistBlend", at="float", min=0, max=1, k=1)
        cmds.addAttr(ln="TwistAnimate", at="float", k=1)
        cmds.addAttr(ln="TwistOffset", at="float", k=1)
        cmds.addAttr(ln=f"{name}"+"UpperLowerCtrl", at="enum", en="---------------", k=1)
        cmds.addAttr(ln="ToggleVisibility", at="float", min=0, max=1, dv=1.0, k=1)      
        # Connect attributes to the sine and twist handles and deformers
        cmds.connectAttr(baseCtrl+".SineBlend", f"{name}"+"_bShape"+f".{name}"+"_sine")
        cmds.connectAttr(baseCtrl+".TwistBlend", f"{name}"+"_bShape"+f".{name}"+"_twist")
        cmds.connectAttr(baseCtrl+".SineAmplitude", f"{ribbonSine}"+"_def"+".amplitude")
        cmds.connectAttr(baseCtrl+".SineWavelength", f"{ribbonSine}"+"_def"+".wavelength")
        cmds.connectAttr(baseCtrl+".SineAnimate", f"{ribbonSine}"+"_def"+".offset")
        cmds.connectAttr(baseCtrl+".SineOffset", sineHandle+transAxis)
        cmds.connectAttr(baseCtrl+".SineDropoff", f"{ribbonSine}"+"_def"+".dropoff")
        cmds.connectAttr(baseCtrl+".TwistAnimate", f"{ribbonTwist}"+"_def"+".startAngle")  
        cmds.connectAttr(baseCtrl+".TwistOffset", twistHandle+transAxis)                                      
        cmds.connectAttr(baseCtrl+".SineOrientation", sineHandle+".rotateY")
        cmds.connectAttr(baseCtrl+".ToggleVisibility", upCtrl+".visibility")
        cmds.connectAttr(baseCtrl+".ToggleVisibility", lowCtrl+".visibility")
        cmds.select(cl=1)
        
        
    def snapHeirarchy(self):
        ''' Creates list of joints to snap to based on user selection '''
        selectionCheck = cmds.ls(sl=1, type="joint")
        if not selectionCheck:
            cmds.error("Please select the root joint of a 3 joint chain")
        else:
            snapRoot = cmds.ls(sl=1, type="joint")[0]
        
        # List is the children of the joint selection            
        heirarchy = cmds.listRelatives(snapRoot, ad=1, type="joint")
        # Ignore joint if the selection list constains a joint ending with "_roll_jnt"      
        jointHeirarchy = (list(filter(lambda x: not x.endswith("_roll_jnt"), heirarchy)))
        jointHeirarchy.append(snapRoot)
        jointHeirarchy.reverse()
        cmds.select(cl=1)
        
        return jointHeirarchy
    
    
    def colourUI(self):
        ''' Enable the altColourText and altColourMenu if altColourCheck is chosen '''
        if cmds.checkBox("altColourCheck", q=1, v=1):
            cmds.text('altColourText', l="Alternate Colour -", e=1, en=1)
            cmds.colorSliderGrp("altColourMenu", e=1, en=1)
        else:
            cmds.text('altColourText', l="Alternate Colour -", e=1, en=0)
            cmds.colorSliderGrp("altColourMenu", e=1, en=0)
            
               
    def ribbonUI(self):
        ''' Creates the UI for the ribbon tool '''
        if cmds.window("ribbonToolUI", ex=1): 
            cmds.deleteUI("ribbonToolUI")
        window = cmds.window("ribbonToolUI", t="Ribbon Builder v1.2", w=200, h=200, mnb=0, mxb=0, s=0, mbr=1)
        mainLayout = cmds.formLayout(nd=100)
        
        # Create items to fill the UI
        titleUI = cmds.text('titleUI', l="Ribbon Builder v1.2", fn="boldLabelFont")
        ribbonTitle = cmds.text('ribbonTitle', l="Ribbon Settings", fn="boldLabelFont")
        controllerTitle = cmds.text('controllerTitle', l="Controller Settings", fn="boldLabelFont")
        snapTitle = cmds.text('snapTitle', l="Joint Snap Settings", fn="boldLabelFont")
        nameText = cmds.text('nameText', l="Ribbon Name -")
        nameMenu = cmds.textField("nameMenu", ann="Please insert name for ribbon", w=100)
        lengthText = cmds.text('lengthText', l="Ribbon Length -")   
        lengthMenu = cmds.floatField("lengthMenu", v=2.5, pre=2, ann="Please type the desired length of the ribbon", w=100)
        scaleText = cmds.text('scaleText', l="Controller Scale -")   
        scaleMenu = cmds.floatField("scaleMenu", v=1.0, pre=2, ann="Multiplier to scale the controllers", w=82)

        directionText = cmds.text('directionText', l="Ribbon Direction -")
        directionMenu = cmds.optionMenu("directionMenu", ann="Select whether the ribbon will be created horizontally or vertically", w=100)
        cmds.menuItem(l="Horizontal")
        cmds.menuItem(l="Vertical")

        axisText = cmds.text('axisText', l="Ribbon Front Axis -")
        axisMenu = cmds.optionMenu("axisMenu", ann="Select the axis for the ribbon to face", w=100)
        cmds.menuItem(l="X", en=0)
        cmds.menuItem(l="Y", en=0)
        cmds.menuItem(l="Z")
        
        jointAxisText = cmds.text('jointAxisText', l="Joint Orient -")
        jointAxisMenu = cmds.optionMenu("jointAxisMenu", ann="Select the axis which the joint chain follows", w=40)
        cmds.menuItem(l="X")
        cmds.menuItem(l="Y")
        cmds.menuItem(l="Z")
        
        colourText = cmds.text('colourText', l="Controller Colour -")
        colourMenu = cmds.colorSliderGrp("colourMenu", rgb=(1,1,1), w=80)
        altColourText = cmds.text('altColourText', l="Alternate Colour -", en=0)
        altColourMenu = cmds.colorSliderGrp("altColourMenu", rgb=(1,1,1), w=80, en=0)
        
        isoparmCheck = cmds.checkBox("isoparmCheck", l="Insert Crease", h=15, ann="Insert additional isoparms at the mid point?")
        visCheck = cmds.checkBox("visCheck", l="Hide ribbon joints", h=15, ann="Make ribbon joints not invisible on creation?")
        follicleCheck = cmds.checkBox("follicleCheck", l="Hide Follicles", h=15, ann="Make ribbon follicles not invisible on creation?")
        snapCheck = cmds.checkBox("snapCheck", l="Snap to Joints", h=15, ann="Snap ribbon to selected joints?")
        snapInvertCheck = cmds.checkBox("snapInvertCheck", l="Invert", h=15, ann="Invert the direction of the axis which the joint chain follows")
        endJointCheck = cmds.checkBox("endJointCheck", l="Orient End to World", h=15, ann="If checked, will orient the final ribbon joint to the world axis, instead of the joint chain")
        altColourCheck = cmds.checkBox("altColourCheck", l="Alternate Colours", h=15, ann="Alternate controller colours?", v=0, cc=self.colourUI)

        separator00 = cmds.separator(h=5)
        separator01 = cmds.separator(h=5)
        separator02 = cmds.separator(h=5)
        separator03 = cmds.separator(h=5)  
              
        button = cmds.button(l="Create Ribbon", c=self.createRibbon)
        
        # UI Layout
        cmds.formLayout(mainLayout, e=1,
                    # af used for items that are central in the window and span its width
                    af = [(titleUI, 'left', 5), (titleUI, 'right', 5), (titleUI, 'top', 5),
                        (separator00, 'left', 5), (separator00, 'right', 5),
                        (ribbonTitle, 'left', 5), (ribbonTitle, 'right', 5), (ribbonTitle, 'top', 5),                    
                        (separator01, 'left', 5), (separator01, 'right', 5),
                        (controllerTitle, 'left', 5), (controllerTitle, 'right', 5), (controllerTitle, 'top', 5),
                        (separator02, 'left', 5), (separator02, 'right', 5),
                        (snapTitle, 'left', 5), (snapTitle, 'right', 5), (snapTitle, 'top', 5),
                        (separator03, 'left', 5), (separator03, 'right', 5),
                        (button, 'bottom', 5), (button, 'left', 5), (button, 'right', 5) 
                    ],
                    # ac sets the vertical placement / order of UI items
                    ac = [(separator00, 'top', 5, titleUI),
                        (ribbonTitle, 'top', 5, separator00),
                        (nameText, 'top', 13, ribbonTitle),
                        (nameMenu, 'top', 10, ribbonTitle),
                        (lengthText, 'top', 13, nameText),
                        (lengthMenu, 'top', 10, nameText),
                        (directionText, 'top', 13, lengthText),
                        (directionMenu, 'top', 10, lengthText),
                        (axisText, 'top', 13, directionText),
                        (axisMenu, 'top', 10, directionText),
                        (axisText, 'top', 13, directionText),
                        (axisMenu, 'top', 10, directionText),
                        (jointAxisText, 'top', 13, axisText),
                        (jointAxisMenu, 'top', 10, axisText),
                        (snapInvertCheck, 'top', 13, axisText),                        
                        (isoparmCheck, 'top', 10, jointAxisText),
                        (visCheck, 'top', 10, isoparmCheck),
                        (follicleCheck, 'top', 10, isoparmCheck),
                        (separator01, 'top', 5, visCheck),
                        (controllerTitle, 'top', 5, separator01),
                        (scaleText, 'top', 13, controllerTitle),
                        (scaleMenu, 'top', 10, controllerTitle),
                        (colourText, 'top', 12, scaleText),
                        (colourMenu, 'top', 10, scaleText),    
                        (altColourCheck, 'top', 12, colourText),
                        (altColourText, 'top', 12, altColourCheck),
                        (altColourMenu, 'top', 10, altColourCheck),                                             
                        (separator02, 'top', 8, altColourMenu),
                        (snapTitle, 'top', 5, separator02),
                        (snapCheck, 'top', 10, snapTitle),
                        (endJointCheck, 'top', 10, snapCheck),
                        (separator03, 'top', 5, endJointCheck),
                        (button, 'top', 5, separator03)
                    ],
                    # ap sets the margin of items not in af
                    ap = [(nameText, 'left', 0, 5),
                        (nameMenu, 'right', -8, 92),
                        (lengthText, 'left', 0, 5),
                        (lengthMenu, 'right', -8, 92),
                        (directionText, 'left', 0, 5),
                        (directionMenu, 'right', -8, 92),
                        (axisText, 'left', 0, 5),
                        (axisMenu, 'right', -8, 92),
                        (jointAxisText, 'left', 0, 5),
                        (jointAxisMenu, 'left', 118, 5),
                        (isoparmCheck, 'left', 0, 5),
                        (visCheck, 'left', 0, 5),
                        (follicleCheck, 'right', 0, 95),
                        (scaleText, 'left', 0, 5),
                        (scaleMenu, 'right', -8, 92),
                        (colourText, 'left', 0, 5),
                        (colourMenu, 'right', -7, 92),
                        (altColourCheck, 'left', 0, 5),
                        (altColourText, 'left', 0, 5),
                        (altColourMenu, 'right', -7, 92),                                           
                        (snapCheck, 'left', 0, 5),
                        (snapInvertCheck, 'right', 0, 95),
                        (endJointCheck, 'left', 0, 5),
                    ]        
        )    
        cmds.showWindow(window)
        cmds.optionMenu('axisMenu', e=1, v='Z')