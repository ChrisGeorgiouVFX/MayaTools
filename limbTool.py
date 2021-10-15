# Auto limb tool

import maya.cmds as cmds

def autoLimbTool(*args):
    # Set up variables which could come from the UI
    
    # Is this an arm (1) or leg (0)?
    whichLimb = cmds.optionMenu("legMenu", q=1, v=1)
    
    if whichLimb == "Arm":
        isArm = 1
    else:
        isArm = 0
        
    # Check the checkboxes
    rollCheck = cmds.checkBox("rollCheck", q=1, v=1)
    
    stretchCheck = cmds.checkBox("stretchCheck", q=1, v=1)    
    
    
    
    # How many joints are we working with
    limbJoints = 3
    
    # Use this information to generate the names
    if isArm:
        limbType = "arm"
        print("Working on the arm")
    else:
        limbType = "leg"
        print("Working on the leg")
        
    # Check the selection is valid
    selectionCheck = cmds.ls(sl=1, type="joint")
    
    # Error check to make sure a joint is selected
    if not selectionCheck:
        cmds.error("Please select the root joint")
    else:
        jointRoot = cmds.ls(sl=1, type="joint")[0]
        
    # Check for indicator of which side the limb is
    limbSide = jointRoot.split("_")[1]
    
    # Usable side check
    if not "L" in limbSide:
        if not "R" in limbSide:
            cmds.error("Please select a joint with either L or R specified")
    
    # Check for joint name
    jointName = jointRoot.split("_")[0]    
    
    # Building the names
    limbName = jointName + "_" + limbSide
        
    mainControl = limbType + "_" + limbSide + "_IK_FK_switch_ctrl"
    ikControl = limbName + "_IK_ctrl"
    fkControl = limbName + "_FK_ctrl"
    kneeControl = limbName + "_pole_ctrl"
    
    
    
    #---------------------------------------------------------------------
    # Build the list of joints we're working with
    
    # Find the children
    jointHeirarchy = cmds.listRelatives(jointRoot, ad=1, type="joint")
    
    # Add selected joint to the list
    jointHeirarchy.append(jointRoot)
    
    # Reverse list
    jointHeirarchy.reverse()
    
    # Clear selection
    cmds.select(cl=1)
    
   
    
    #---------------------------------------------------------------------
    # Duplicate the main joint chain and rename the joints
    
    # Define the joint chains
    newJointList = ["_IK_jnt", "_FK_jnt", "_stretch_jnt"]
    
    # Build the joints
    for newJoint in newJointList:
        for i in range(limbJoints):
            newJointName = jointHeirarchy[i].replace("_jnt", newJoint)
            
            cmds.joint(n=newJointName, rad=0.5)
            cmds.matchTransform(newJointName, jointHeirarchy[i])
            cmds.makeIdentity(newJointName, a=1, t=0, r=1, s=0,)
            
        cmds.select(cl=1)



    #---------------------------------------------------------------------
    # Constrain main joint chain to IK and FK
    for i in range(limbJoints):
        cmds.parentConstraint( (jointHeirarchy[i].replace("_jnt", "_IK_jnt")), (jointHeirarchy[i].replace("_jnt", "_FK_jnt")), jointHeirarchy[i], w=1, mo=0 )



    #---------------------------------------------------------------------
    # Setup FK
    # Connect FK controls to joints
    for i in range(limbJoints):
        cmds.parentConstraint( (jointHeirarchy[i].replace("_jnt", "_FK_ctrl")), (jointHeirarchy[i].replace("_jnt", "_FK_jnt")), w=1, mo=0 )



    #---------------------------------------------------------------------
    # Setup IK
    # Create IK handle between the root and end joint
    cmds.ikHandle( n=(limbType + "_" + limbSide + "_IK_handle"), sol="ikRPsolver", sj=(jointHeirarchy[0].replace("_jnt", "_IK_jnt")), ee=(jointHeirarchy[2].replace("_jnt", "_IK_jnt")))

    # Adjust heirarchy so that IK controller drives the IK handle
    cmds.parent( (limbType + "_" + limbSide + "_IK_handle"), (jointHeirarchy[2].replace("_jnt", "_IK_ctrl")) )

    # Made the IK control drive the joint to maintain orientation
    cmds.orientConstraint( jointHeirarchy[2].replace("_jnt", "_IK_ctrl"), jointHeirarchy[2].replace("_jnt", "_IK_jnt"), w=1)

    # Add pole vector to the IK joint
    cmds.poleVectorConstraint( (jointHeirarchy[1].replace("_jnt", "_pole_ctrl")), (limbType + "_" + limbSide + "_IK_handle"), w=1 )



    #---------------------------------------------------------------------
    # Blend between FK and IK
    for i in range(limbJoints):
        getConstraint = cmds.listConnections( (jointHeirarchy[i]), type="parentConstraint") [0]
        getWeights = cmds.parentConstraint(getConstraint, q=1, wal=1)

        cmds.connectAttr( (mainControl + "." + limbType + "_" + limbSide + "_IK_FK_switch_CTRL"), (getConstraint + "." + getWeights[1]), f=1)
        cmds.connectAttr( ((limbType + "_" + limbSide) + "_IK_FK_reverse.outputX"), (getConstraint + "." + getWeights[0]), f=1)



    #---------------------------------------------------------------------
    # Update heirarchy

    # Make new joints not visible
    cmds.setAttr( (jointRoot.replace("_jnt", "_IK_jnt") + ".visibility"), 0)
    cmds.setAttr( (jointRoot.replace("_jnt", "_FK_jnt") + ".visibility"), 0)
    cmds.setAttr( (jointRoot.replace("_jnt", "_stretch_jnt") + ".visibility"), 0)
    
    # Place new joints into joint heirarchy
    if isArm:
        cmds.parent( (jointRoot.replace("_jnt", "_IK_jnt")), (jointRoot.replace("_jnt", "_FK_jnt")), (jointRoot.replace("_jnt", "_stretch_jnt")), "clavicle_" + limbSide + "_jnt")
    else:  
        cmds.parent( (jointRoot.replace("_jnt", "_IK_jnt")), (jointRoot.replace("_jnt", "_FK_jnt")), (jointRoot.replace("_jnt", "_stretch_jnt")), "root_jnt")

    # clear selection
    cmds.select(cl=1)



    #---------------------------------------------------------------------
    # Stretchy Limbs
    
    if stretchCheck:
    
        # Variable for the locator at the end of the joint chain
        stretchEndPosLoc = jointRoot.replace("_jnt", "_stretchEndPos_loc")

        # Create locator used to calculate limb length
        cmds.spaceLocator( n=stretchEndPosLoc )
        cmds.setAttr( (stretchEndPosLoc + ".visibility"), 0)
            
        # Place locator at the end of the limb chain and parent to controller
        cmds.matchTransform(stretchEndPosLoc, jointHeirarchy[2])
        cmds.parent(stretchEndPosLoc, jointHeirarchy[2].replace("_jnt", "_IK_ctrl"))
        
        # Start building the distance nodes
        # Add all the distance nodes together using a plusMinusAverage node
        cmds.shadingNode("plusMinusAverage", au=1, n=jointRoot.replace("_jnt", "_length"))
        
        # Build distance nodes for each section
        for i in range(limbJoints):
            
            # Ignore the lat joint or it will try to include the fingers / toes
            if i is not limbJoints -1:
                cmds.shadingNode("distanceBetween", au=1, n=jointHeirarchy[i].replace("_jnt", "_distNode"))
                
                cmds.connectAttr( jointHeirarchy[i].replace("_jnt", "_stretch_jnt.worldMatrix"), jointHeirarchy[i].replace("_jnt", "_distNode.inMatrix1"), f=1)
                cmds.connectAttr( jointHeirarchy[i+1].replace("_jnt", "_stretch_jnt.worldMatrix"), jointHeirarchy[i].replace("_jnt", "_distNode.inMatrix2"), f=1)
                
                cmds.connectAttr( jointHeirarchy[i].replace("_jnt", "_stretch_jnt.rotatePivotTranslate"), jointHeirarchy[i].replace("_jnt", "_distNode.point1"), f=1)
                cmds.connectAttr( jointHeirarchy[i+1].replace("_jnt", "_stretch_jnt.rotatePivotTranslate"), jointHeirarchy[i].replace("_jnt", "_distNode.point2"), f=1)

                
                cmds.connectAttr( jointHeirarchy[i].replace("_jnt", "_distNode.distance"), jointRoot.replace("_jnt", "_length.input1D[" + str(i) + "]"), f=1)


        # Get distance between the root and stretch end locator to check if stretching
        cmds.shadingNode( "distanceBetween", au=1, n=jointRoot.replace("_jnt", "_stretchDistNode"))

        cmds.connectAttr( jointHeirarchy[0].replace("_jnt", "_stretch_jnt.worldMatrix"), (limbName +  "_stretchDistNode.inMatrix1"), f=1)
        cmds.connectAttr( (stretchEndPosLoc + ".worldMatrix"), (limbName +  "_stretchDistNode.inMatrix2"), f=1)
                
        cmds.connectAttr( jointHeirarchy[0].replace("_jnt", "_stretch_jnt.rotatePivotTranslate"), (limbName + "_stretchDistNode.point1"), f=1)
        cmds.connectAttr( (stretchEndPosLoc + ".rotatePivotTranslate"), (limbName + "_stretchDistNode.point2"), f=1)

        # Create nodes to check for stretching and control if needed
        
        # Scale factor compared the length of the leg, with the length of the stretch locator to see if the leg is stretching
        cmds.shadingNode( "multiplyDivide", au=1, n=jointRoot.replace("_jnt", "_scaleFactor"))  
        
        # Conditional node to pass this onto the objects, to control how the leg stretches
        cmds.shadingNode( "condition", au=1, n=jointRoot.replace("_jnt", "_condition"))  
        
        # Adjust node settings
        cmds.setAttr(jointRoot.replace("_jnt", "_condition.operation"), 2)
        cmds.setAttr(jointRoot.replace("_jnt", "_condition.secondTerm"), 1)    
        
        cmds.setAttr(jointRoot.replace("_jnt", "_scaleFactor.operation"), 2)

        # Connect the stretch distance to the scale factor multiply divide node
        cmds.connectAttr( (limbName +  "_stretchDistNode.distance"), jointRoot.replace("_jnt", "_scaleFactor.input1X"), f=1)
        
        # Connect the full leg distance to the scale factor multiply divide node
        cmds.connectAttr( jointRoot.replace("_jnt", "_length.output1D"), jointRoot.replace("_jnt", "_scaleFactor.input2X"), f=1)   

        # Connect the scale factor node to the condition node
        cmds.connectAttr( jointRoot.replace("_jnt", "_scaleFactor.outputX"), jointRoot.replace("_jnt", "_condition.firstTerm"), f=1)

        # Also connect to the color if true attribute, so we can use it as a stretch value
        cmds.connectAttr( jointRoot.replace("_jnt", "_scaleFactor.outputX"), jointRoot.replace("_jnt", "_condition.colorIfTrueR"), f=1)

        # Connect the consition node to the IK leg joints
        for i in range(limbJoints):
            cmds.connectAttr( jointRoot.replace("_jnt", "_condition.outColorR"), jointHeirarchy[i].replace("_jnt", "_IK_jnt.scaleY"), f=1)        

        # Ability to blend between the stretchiness
        cmds.shadingNode( "blendColors", au=1, n=jointRoot.replace("_jnt", "_blendColors")) 
        cmds.setAttr( jointRoot.replace("_jnt", "_blendColors.color2"), 1, 0, 0, type="double3" )  

        cmds.connectAttr( jointRoot.replace("_jnt", "_scaleFactor.outputX"), jointRoot.replace("_jnt", "_blendColors.color1R"), f=1) 
        cmds.connectAttr( jointRoot.replace("_jnt", "_blendColors.outputR"), jointRoot.replace("_jnt", "_condition.colorIfTrueR"), f=1) 
        
        # Connect to the paw control attribute
        cmds.connectAttr( jointHeirarchy[2].replace("_jnt", "_IK_ctrl.Stretchiness"), jointRoot.replace("_jnt", "_blendColors.blender"), f=1) 
        
        # Wire up the attributes so we can control how the stretch works
        cmds.setAttr( jointHeirarchy[2].replace("_jnt", "_IK_ctrl.StretchType"), 0 )
        cmds.setAttr( jointRoot.replace("_jnt", "_condition.operation"), 1 )  # Not equal (Squash and stretch)
        
        cmds.setDrivenKeyframe( jointRoot.replace("_jnt", "_condition.operation"), cd=jointHeirarchy[2].replace("_jnt", "_IK_ctrl.StretchType") )

        cmds.setAttr( jointHeirarchy[2].replace("_jnt", "_IK_ctrl.StretchType"), 1 )
        cmds.setAttr( jointRoot.replace("_jnt", "_condition.operation"), 3 )  # Greater than (Stretch only)
        
        cmds.setDrivenKeyframe( jointRoot.replace("_jnt", "_condition.operation"), cd=jointHeirarchy[2].replace("_jnt", "_IK_ctrl.StretchType") )

        cmds.setAttr( jointHeirarchy[2].replace("_jnt", "_IK_ctrl.StretchType"), 2 )
        cmds.setAttr( jointRoot.replace("_jnt", "_condition.operation"), 5 )  # Less or equal (Squash only)
        
        cmds.setDrivenKeyframe( jointRoot.replace("_jnt", "_condition.operation"), cd=jointHeirarchy[2].replace("_jnt", "_IK_ctrl.StretchType") )
        
        cmds.setAttr( jointHeirarchy[2].replace("_jnt", "_IK_ctrl.StretchType"), 1 )

        # clear selection
        cmds.select(cl=1)
        
        
        
        #---------------------------------------------------------------------
        # Volume Preservation
        
        # Create the main multiply divide node which with calculate the volume
        cmds.shadingNode( "multiplyDivide", au=1, n=jointRoot.replace("_jnt", "_volume"))
        
        # Set opperation to power
        cmds.setAttr( jointRoot.replace("_jnt", "_volume.operation"), 3 )
        
        # Connect main stretch value to the volume node
        cmds.connectAttr( jointRoot.replace("_jnt", "_blendColors.outputR"), jointRoot.replace("_jnt", "_volume.input1X"), f=1) 
        
        # Connect to the condition node to control the scaling
        cmds.connectAttr( jointRoot.replace("_jnt", "_volume.outputX"), jointRoot.replace("_jnt", "_condition.colorIfTrueG"), f=1)    
        
        # Connect to the limb joints
        cmds.connectAttr( jointRoot.replace("_jnt", "_condition.outColorG"), jointHeirarchy[1] + ".scaleX", f=1)
        cmds.connectAttr( jointRoot.replace("_jnt", "_condition.outColorG"), jointHeirarchy[1] + ".scaleZ", f=1)
         
        cmds.connectAttr( jointRoot.replace("_jnt", "_condition.outColorG"), jointHeirarchy[2] + ".scaleX", f=1)
        cmds.connectAttr( jointRoot.replace("_jnt", "_condition.outColorG"), jointHeirarchy[2] + ".scaleZ", f=1)
        
        # Connect to main volume attribute control
        cmds.connectAttr( (mainControl + ".Volume_Offset"), jointRoot.replace("_jnt", "_volume.input2X"), f=1)



    #---------------------------------------------------------------------
    # Roll joint systems
    
    if rollCheck:
    
        # Check which side we are working on so we can move things to the correct side
        if limbSide == "L":
            flipSide = 1
        else:
            flipSide = -1

        # Create the main roll and follow joints
        rollJointList = [ jointHeirarchy[0], jointHeirarchy[2], jointHeirarchy[0], jointHeirarchy[0]] 

        for i in range(len(rollJointList)):
            
            if i > 2:
                rollJointName = rollJointList[i].replace("_jnt", "_follow_tip_jnt")
            elif i > 1:
                rollJointName = rollJointList[i].replace("_jnt", "_follow_jnt")
            else :
                rollJointName = rollJointList[i].replace("_jnt", "_roll_jnt")
                
            cmds.joint(n=rollJointName, rad=0.6)
            cmds.matchTransform(rollJointName, rollJointList[i])
            cmds.makeIdentity(rollJointName, a=1, t=0, r=1, s=0,)
            
            if i < 2:
                cmds.parent( rollJointName, rollJointList[i])
            elif i > 2:
                cmds.parent( rollJointName, rollJointList[2].replace("_jnt", "_follow_jnt"))
                
            cmds.select(cl=1)

            # Show roational axes to help visualise rotations
            # cmds.toggle( rollJointName, la=1)



        #---------------------------------------------------------------------
        # Upper limb systems
       
        # Adjust the follow joints at the base of the joint chain
        cmds.pointConstraint( jointHeirarchy[0], jointHeirarchy[1], rollJointList[2].replace("_jnt", "_follow_tip_jnt"), w=1, mo=0, n="tempPC" )
        cmds.delete("tempPC")
        
        # Move the follow joints out to the side
        cmds.move( 0.8*flipSide, 0, 0, rollJointList[2].replace("_jnt", "_follow_jnt"), r=1, os=1, wd=1 )
        
        # Create the locator which the roll joint will always follow
        cmds.spaceLocator( n=rollJointList[0].replace("_jnt", "_roll_aim_loc") )
        
        # Move locator to the root joint, match it's transformations and parent to the follow joint
        cmds.matchTransform(rollJointList[0].replace("_jnt", "_roll_aim_loc"), rollJointList[2].replace("_jnt", "_follow_jnt"))
        cmds.parent( rollJointList[0].replace("_jnt", "_roll_aim_loc"), rollJointList[2].replace("_jnt", "_follow_jnt"))

        # Move the locator out to the side
        cmds.move( 0.8*flipSide, 0, 0, rollJointList[0].replace("_jnt", "_roll_aim_loc"), r=1, os=1, wd=1 )

        # Make the root joint aim down the joint chain, but keep looking at the aim locator for reference
        cmds.aimConstraint( jointHeirarchy[1], rollJointList[0].replace("_jnt", "_roll_jnt"), w=1, aim=(0, -1, 0), u=(1, 0, 0), wut="object", wuo=rollJointList[0].replace("_jnt", "_roll_aim_loc"), mo=1 )

        # Make the IK handle for the follow joints
        cmds.ikHandle( n=(limbType + "_" + limbSide + "_follow_IK_handle"), sol="ikRPsolver", sj=rollJointList[2].replace("_jnt", "_follow_jnt"), ee=rollJointList[2].replace("_jnt", "_follow_tip_jnt"))
        
        # Move the handle down to the next joint in the chain (elbow or knee) to that it follows it
        cmds.parent( limbType + "_" + limbSide + "_follow_IK_handle", jointHeirarchy[1])   
        cmds.matchTransform( limbType + "_" + limbSide + "_follow_IK_handle", jointHeirarchy[1])
        
        # Reset the pole vector so it doesnt rotate around the limb axis
        cmds.setAttr( (limbType + "_" + limbSide + "_follow_IK_handle.poleVectorZ"), 0)
        cmds.setAttr( (limbType + "_" + limbSide + "_follow_IK_handle.poleVectorX"), 0)
        cmds.setAttr( (limbType + "_" + limbSide + "_follow_IK_handle.poleVectorY"), 0)
        
        

        #---------------------------------------------------------------------
        # Lower limb systems

        # Create the locator which the roll joint will always follow
        cmds.spaceLocator( n=rollJointList[1].replace("_jnt", "_roll_aim_loc") )

        # Move locator to the root joint, match it's transformations and parent to the follow joint
        cmds.matchTransform(rollJointList[1].replace("_jnt", "_roll_aim_loc"), rollJointList[1].replace("_jnt", "_roll_jnt"))
        cmds.parent( rollJointList[1].replace("_jnt", "_roll_aim_loc"), jointHeirarchy[2])

        # Move the locator out to the side
        cmds.move( 0.8*flipSide, 0, 0, rollJointList[1].replace("_jnt", "_roll_aim_loc"), r=1, os=1, wd=1 )
          
        # Make the wrist / ankle joint aim up the joint chain, but keep looking at the aim locator for reference
        cmds.aimConstraint( jointHeirarchy[1], rollJointList[1].replace("_jnt", "_roll_jnt"), w=1, aim=(0, 1, 0), u=(1, 0, 0), wut="object", wuo=rollJointList[1].replace("_jnt", "_roll_aim_loc"), mo=1 )
        
        # Update heirarchy to parent the follow joints to the main group  
        if cmds.objExists("systems"):  # If the systems group exists
            cmds.parentConstraint( "master_ctrl", "systems",  w=1, mo=1 ) # Parent constraint systems as a child of master_ctrl
            cmds.parent( rollJointList[2].replace("_jnt", "_follow_jnt"), "systems")  # Parent the follow joint chain under systems
            
            if isArm:
                cmds.parentConstraint( "chest_jnt", rollJointList[2].replace("_jnt", "_follow_jnt"),  w=1, mo=1 )  # If working on the arm parent constrain the roll follow joint to the chest joint
                
            else:
                cmds.parentConstraint( "root_jnt", rollJointList[2].replace("_jnt", "_follow_jnt"),  w=1, mo=1 )  # If working on the leg parent constrain the roll follow joint to the root joint

        else:
            cmds.group( em=True, n="systems" )  # Create the systems group
            cmds.parentConstraint( "master_ctrl", "systems",  w=1, mo=1 ) # Parent constraint systems as a child of master_ctrl
            cmds.parent( rollJointList[2].replace("_jnt", "_follow_jnt"), "systems")  # Parent the follow joint chain under systems

            if isArm:
                cmds.parentConstraint( "chest_jnt", rollJointList[2].replace("_jnt", "_follow_jnt"),  w=1, mo=1 )  # If working on the arm parent constrain the roll follow joint to the chest joint
                
            else:
                cmds.parentConstraint( "root_jnt", rollJointList[2].replace("_jnt", "_follow_jnt"),  w=1, mo=1 )  # If working on the leg parent constrain the roll follow joint to the root joint

        cmds.setAttr( "systems.visibility", 0)  # Make the systems group non visible
        cmds.select(cl=1)
    

#---------------------------------------------------------------------
# Creates the Ui for the auto limb tool
    
def autoLimbToolUI():    
    
    # Check if UI is already open, if so close it
    if cmds.window("autoLimbToolUI", ex=1): cmds.deleteUI("autoLimbToolUI")
    
    # Create the window
    window = cmds.window("autoLimbToolUI", t="Auto Limb Tool v1.0", w=200, h=200, mnb=0, mxb=0)

    # Create the layout of the window
    mainLayout = cmds.formLayout(nd=100)
    
    # Limb menu
    limbMenu = cmds.optionMenu("legMenu", l="Which limb?", h=20, ann="Are you planning to rig the arm or leg?")
    
    cmds.menuItem(l="Arm")
    cmds.menuItem(l="Leg")
    
    # Checkboxes
    rollCheck = cmds.checkBox("rollCheck", l="Roll joints?", h=20, ann="Generate roll joints?", v=0)
    stretchCheck = cmds.checkBox("stretchCheck", l="Stretchy?", h=20, ann="Generate stretchy limbs?", v=0)
    
    # Separators
    separator01 = cmds.separator(h=5)
    separator02 = cmds.separator(h=5)
    
    # Buttons
    button = cmds.button(l="Rig Limb", c=autoLimbTool)
    
    # Adjust layout
    cmds.formLayout(mainLayout, e=1,
                af = [(limbMenu, 'top', 5), (limbMenu, 'left', 5), (limbMenu, 'right', 5),
                    (separator01, 'left', 5), (separator01, 'right', 5),
                    (separator02, 'left', 5), (separator02, 'right', 5),
                    (button, 'bottom', 5), (button, 'left', 5), (button, 'right', 5)                
                ],
                
                ac = [(separator01, 'top', 5, limbMenu),
                    (rollCheck, 'top', 5, separator01),
                    (stretchCheck, 'top', 5, separator01),
                    (separator02, 'top', 5, rollCheck),
                    (button, 'top', 5, separator02)
                ],
                
                ap = [(rollCheck, 'left', 0, 15),
                    (stretchCheck, 'right', 0, 85)                   
                    
                ]
    )
    
    
    # Show the window
    cmds.showWindow(window)