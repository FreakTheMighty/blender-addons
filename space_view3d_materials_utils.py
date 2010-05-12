#(c) 2010 Michael Williamson (michaelw)
#ported from original by Michael Williamsn
#
#tested r28370
#
#
# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_addon_info = {
    'name': '3D View: Material Utils',
    'author': 'michaelw',
    'version': '0.9',
    'blender': (2, 5, 3),
    'location': 'View3D > Q key',
    'description': 'Menu of material tools (assign, select by etc)  in the 3D View',
    'url':
    'http://wiki.blender.org/index.php/Extensions:2.5/Py/' \
        'Scripts',  # @todo Create wiki page and fix this link.
    'category': '3D View'}
"a menu of material tools"

"""
Name: 'Master Material Menu'
Blender: 253
"""

__author__ = ["michaelW"]
__version__ = '1.3'
__url__ = [""]
__bpydoc__ = """
this script has several functions and operators... grouped for convenience
* assign material:
    offers the user a list of ALL the materials in the blend file and an additional "new" entry
    the chosen material will be assigned to all the selected objects in object mode.
    
    in edit mode the selected faces get the selected material applied.

    if the user chose "new" the new material can be renamed using the "last operator" section of the toolbox
    After assigning the material "clean material slots" and "material to texface" are auto run to keep things tidy (see description bellow)


*select by material
    in object mode this offers the user a menu of all materials in the blend file
    any objects using the selected material will become selected, any objects without the material will be removed from selection.
    
    in edit mode:  the menu offers only the materials attached to the current object. It will select the faces that use the material and deselect those that do not.

*clean material slots
    for all selected objects any empty material slots or material slots with materials that are not used by the mesh faces will be removed.

*


 Any un-used materials and slots will be removed 
"""



import bpy
from bpy.props import*


def replace_material(m1 , m2, all_objects = False):
    #replace material named m1 with material named m2
    #m1 is the name of original material
    #m2 is the name of the material to replace it with
    #'all' will replace throughout the blend file
    try:
        matorg = bpy.data.materials[m1]
        matrep = bpy.data.materials[m2]
        
        
        #store active object
        scn = bpy.context.scene
        ob_active = bpy.context.active_object
        
        if all_objects:
            objs = bpy.data.objects
        
        else:
            objs = bpy.context.selected_editable_objects
        
        for ob in objs:
            if ob.type == 'MESH':
                scn.objects.active = ob
                print(ob.name)   
                ms = ob.material_slots.values()
            
                for m in ms:
                    if m.material == matorg:
                        m.material = matrep
                        #don't break the loop as the material can be 
                        # ref'd more than once
        
        #restore active object
        scn.objects.active = ob_active
    except:
        print('no match to replace')

def select_material_by_name(find_mat):
    #in object mode selects all objects with material find_mat
    #in edit mode selects all faces with material find_mat
    
    #check for editmode
    editmode = False

    scn = bpy.context.scene
    actob = bpy.context.active_object
    if actob.mode == 'EDIT':
        editmode =True
        bpy.ops.object.mode_set()
    
    
    if not editmode:
        objs = bpy.data.objects 
        for ob in objs:
            if ob.type == 'MESH':
                ms = ob.material_slots.values()
                for m in ms:
                    if m.material.name == find_mat:
                        ob.selected = True
                        #the active object may not have the mat!
                        #set it to one that does!
                        scn.objects.active = ob
                        break
                    else:
                        ob.selected = False
                            
            #deselect non-meshes                
            else:
                ob.selected = False
    
    else:
        #it's editmode, so select the faces
        ob = actob
        ms = ob.material_slots.values()
    
        #same material can be on multiple slots
        slot_indeces =[]
        i = 0
        found = False
        for m in ms:
            if m.material.name == find_mat:
                slot_indeces.append(i)
                found = True
        me = ob.data
        for f in me.faces:
            if f.material_index in slot_indeces:
                f.selected = True
            else:
                f.selected = False
        me.update   
    if editmode:
        bpy.ops.object.mode_set(mode = 'EDIT')

def mat_to_texface():
    #assigns the first image in each material to the faces in the active uvlayer
    #for all selected objects
    
    #check for editmode
    editmode = False
    
    actob = bpy.context.active_object
    if actob.mode == 'EDIT':
        editmode =True
        bpy.ops.object.mode_set()
    
    for ob in bpy.context.selected_editable_objects:
        #get the materials from slots
        ms = ob.material_slots.values()
        
        #build a list of images, one per material
        images=[]
        #get the textures from the mats
        for m in ms:
            gotimage = False
            textures = m.material.texture_slots.values()
            if len(textures) >= 1:
                for t in textures:
                    if t != None:
                        tex = t.texture
                        if tex.type == 'IMAGE':
                            img = tex.image
                            images.append(img)
                            gotimage =True
                            break
    
            if not gotimage:
                print('noimage on', m.name)
                images.append(None)
    
        #now we have the images
        #applythem to the uvlayer
    
        
        me = ob.data
        #got uvs?
        if not me.uv_textures:
            scn = bpy.context.scene
            scn.objects.active = ob
            bpy.ops.mesh.uv_texture_add()
            scn.objects.active = actob
        
        #get active uvlayer
        for t in  me.uv_textures:
            if t.active:
                uvtex = t.data.values()
                for f in me.faces:
                    #check that material had an image!
                    if images[f.material_index] != None:
                        uvtex[f.index].image = images[f.material_index]
                        uvtex[f.index].tex =True
                    else:
                        uvtex[f.index].tex =False
    
        me.update
        
    
    if editmode:
        bpy.ops.object.mode_set(mode = 'EDIT')
                    
        

def assignmatslots(ob, matlist):
    #given an object and a list of material names
    #removes all material slots form the object
    #adds new ones for each material in matlist
    #adds the materials to the slots as well.

    scn = bpy.context.scene
    ob_active = bpy.context.active_object
    scn.objects.active = ob

    for s in ob.material_slots:
        bpy.ops.object.material_slot_remove()


    #re-add them and assign material
    i = 0
    for m in matlist:
        mat = bpy.data.materials[m]
        bpy.ops.object.material_slot_add()
        ob.material_slots.values()[i].material = mat
        i += 1

    #restore active object:
    scn.objects.active = ob_active


def cleanmatslots():
    #check for edit mode
    editmode = False
    actob = bpy.context.active_object
    if actob.mode == 'EDIT':
        editmode =True
        bpy.ops.object.mode_set()


    objs = bpy.context.selected_editable_objects
    
    for ob in objs:
        print(ob.name)    
        mats = ob.material_slots.keys()
    
        #check the faces on the mesh to build a list of used materials
        usedMatIndex =[]        #we'll store used materials indices here
        faceMats =[]    
        me = ob.data
        for f in me.faces:
            #get the material index for this face...
            faceindex = f.material_index
                    
            #indices will be lost: Store face mat use by name
            currentfacemat = mats[faceindex]
            faceMats.append(currentfacemat)
                    
                    
            #check if index is already listed as used or not
            found = 0
            for m in usedMatIndex:
                if m == faceindex:
                    found = 1
                    #break
                        
            if found == 0:
            #add this index to the list     
                usedMatIndex.append(faceindex)
    
        #re-assign the used mats to the mesh and leave out the unused
        ml = []
        mnames = []
        for u in usedMatIndex:
            ml.append( mats[u] )
            #we'll need a list of names to get the face indices...
            mnames.append(mats[u])
                    
        assignmatslots(ob, ml)
        
                
        #restore face indices:
        i = 0
        for f in me.faces:
            matindex = mnames.index(faceMats[i])
            f.material_index = matindex
            i += 1
        print('Done')
    if editmode:
        bpy.ops.object.mode_set(mode = 'EDIT')





def assign_mat(matname="Default"): 
    #get active object so we can restore it later
    actob = bpy.context.active_object
    
    #check if material exists, if it doesn't then create it
    mats =bpy.data.materials
    found = False
    for m in mats:
        if m.name == matname:
            target = m
            found = True
            break
    if not found:
        target = bpy.data.materials.new(matname)
    
    
    #if objectmodeset all faces
    editmode = False
    allfaces = True
    if actob.mode == 'EDIT':
        editmode =True
        allfaces = False    
        bpy.ops.object.mode_set()
    
    objs = bpy.context.selected_editable_objects
    
    for ob in objs:    
        #set the active object to our object
        scn = bpy.context.scene
        scn.objects.active = ob
        
    
        #check if the material is on the object already
        if ob.type =='MESH':
            #check material slots for matname material
            found=False
            i = 0
            mats = ob.material_slots
            for m in mats:
                if m.name == matname:
                    found =True
                    index = i
                    #make slot active
                    ob.active_material_index = i
                    break
                i += 1
            
            if not found:
                index=i
                #the material is not attached to the object 
                #so attach it!
    
                #add a material slot
                bpy.ops.object.material_slot_add()
    
                #make  slot active
                ob.active_material_index = i
    
                #and assign material to slot
                ob.material_slots.values()[i].material = target
            #now assign the material:
            me =ob.data
            if allfaces:
                for f in me.faces:
                    f.material_index = index
            elif allfaces == False:
                for f in me.faces:
                    if f.selected:
                        f.material_index = index
            me.update

    #restore the active object
    bpy.context.scene.objects.active = actob
    if editmode:
        bpy.ops.object.mode_set(mode = 'EDIT')

def texface_to_mat():
    
    for ob in bpy.context.selected_editable_objects:
        img = 0
        m = 0
        #get Image from active_uv_texture
        if (ob.data.uv_textures
        and ob.data.active_uv_texture.data[0].image):
            img = ob.data.active_uv_texture.data[0].image
        #if not look in other uv_textures, take first one
        else:
            for uv_tex in ob.data.uv_textures:
                if uv_tex.data[0].image:
                    img = uv_tex.data[0].image
                    break
        
        #get material to assign image to if object has an image in uv_textures
        if img:
            #get active material
            if ob.active_material:
                m = ob.active_material
            #if not look if there are others, take first one
            if not m and ob.material_slots:
                ms = ob.material_slots.values()
                for matslot in ms:
                    if matslot.material:
                        m = matslot.material
                        break
        
        #if ob has no material but we have an image create a material
        if not m and img:
            m = bpy.data.materials.new(name=img.name)
            ob.data.add_material(m)

        #if image is there create texture and apply to material
        if img:
            tex = bpy.data.textures.new(name=img.name)
            tex.type = 'IMAGE'
            tex = tex.recast_type()
            tex.image = img
            m.add_texture(tex, texture_coordinates='UV', map_to='COLOR')

#operator classes:
#---------------------------------------------------------------------

class VIEW3D_OT_texface_to_material(bpy.types.Operator):
    ''''''
    bl_idname = "texface_to_material"
    bl_label = "MW Texface Images to Material/Texture"
    bl_options = {'REGISTER', 'UNDO'}

    def poll(self, context):
        return context.active_object != None

    def execute(self, context):
        texface_to_mat()
        return {'FINISHED'}

class VIEW3D_OT_assign_material(bpy.types.Operator):
    '''assign a material to the selection'''
    bl_idname = "assign_material"
    bl_label = "MW Assign Material"
    bl_options = {'REGISTER', 'UNDO'}

    matname = StringProperty(name = 'Material Name', 
        description = 'Name of Material to Assign', 
        default = "", maxlen = 21)
    
    def poll(self, context):
        return context.active_object != None

    def execute(self, context):
        mn = self.properties.matname
        print(mn)
        assign_mat(mn)
        cleanmatslots()
        mat_to_texface()
        return {'FINISHED'}

class VIEW3D_OT_clean_material_slots(bpy.types.Operator):
    '''removes any material slots from the 
    selected objects that are not used by the mesh'''
    bl_idname = "clean_material_slots"
    bl_label = "MW Clean Material Slots"
    bl_options = {'REGISTER', 'UNDO'}

    def poll(self, context):
        return context.active_object != None

    def execute(self, context):
        cleanmatslots()
        return {'FINISHED'}

class VIEW3D_OT_material_to_texface(bpy.types.Operator):
    ''''''
    bl_idname = "material_to_texface"
    bl_label = "MW Material Images to Texface"
    bl_options = {'REGISTER', 'UNDO'}

    def poll(self, context):
        return context.active_object != None

    def execute(self, context):
        mat_to_texface()
        return {'FINISHED'}

class VIEW3D_OT_select_material_by_name(bpy.types.Operator):
    ''''''
    bl_idname = "select_material_by_name"
    bl_label = "MW Select Material By Name"
    bl_options = {'REGISTER', 'UNDO'}
    matname = StringProperty(name = 'Material Name', 
        description = 'Name of Material to Select', 
        default = "", maxlen = 21)

    def poll(self, context):
        return context.active_object != None

    def execute(self, context):
        mn = self.properties.matname
        select_material_by_name(mn)
        return {'FINISHED'}


class VIEW3D_OT_replace_material(bpy.types.Operator):
    '''assign a material to the selection'''
    bl_idname = "replace_material"
    bl_label = "MW Replace Material"
    bl_options = {'REGISTER', 'UNDO'}

    matorg = StringProperty(name = 'Material to Replace', 
        description = 'Name of Material to Assign', 
        default = "", maxlen = 21)

    matrep = StringProperty(name = 'Replacement material', 
        description = 'Name of Material to Assign', 
        default = "", maxlen = 21)

    all_objects = BoolProperty(name ='all_objects',
        description="replace for all objects in this blend file",
        default = True)
    
    def poll(self, context):
        return context.active_object != None

    def execute(self, context):
        m1 = self.properties.matorg
        m2 = self.properties.matrep
        all = self.properties.all_objects
        replace_material(m1,m2,all)
        return {'FINISHED'}

#menu classes
#-------------------------------------------------------------------------------
class VIEW3D_MT_master_material(bpy.types.Menu):
    bl_label = "Master Material Menu"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.menu("VIEW3D_MT_assign_material", icon='ZOOMIN')
        layout.menu("VIEW3D_MT_select_material", icon='HAND')
        layout.separator()
        layout.operator("clean_material_slots", 
            text = 'Clean Material Slots', icon='CANCEL')
        layout.operator("material_to_texface",
            text = 'Material to Texface',icon='FACESEL_HLT')
        layout.operator("texface_to_material",
            text = 'Texface to Material',icon='FACESEL_HLT')

        layout.separator()
        layout.operator("replace_material", 
            text = 'Replace Material', icon='ARROW_LEFTRIGHT')
       


class VIEW3D_MT_assign_material(bpy.types.Menu):
    bl_label = "Assign Material"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        ob = context
        layout.label
        for i in range (len(bpy.data.materials)):
    
            layout.operator("assign_material",
                text=bpy.data.materials[i].name, 
                icon='MATERIAL_DATA').matname = bpy.data.materials[i].name

        layout.operator("assign_material",text="Add New", 
                icon='ZOOMIN')

class VIEW3D_MT_select_material(bpy.types.Menu):
    bl_label = "Select by Material"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        ob = context.object
        layout.label
        if ob.mode == 'OBJECT':
            #show all materials in entire blend file
            for i in range (len(bpy.data.materials)):
        
                layout.operator("select_material_by_name",
                    text=bpy.data.materials[i].name, 
                    icon='MATERIAL_DATA').matname = bpy.data.materials[i].name


        elif ob.mode == 'EDIT':
            #show only the materials on this object
            mats = ob.material_slots.keys()
            for m in mats:
                layout.operator("select_material_by_name",
                    text=m, 
                    icon='MATERIAL_DATA').matname = m




       

classes = [
VIEW3D_OT_assign_material,
VIEW3D_OT_clean_material_slots,
VIEW3D_OT_material_to_texface,
VIEW3D_OT_select_material_by_name,
VIEW3D_OT_replace_material,
VIEW3D_OT_texface_to_material,
VIEW3D_MT_master_material,
VIEW3D_MT_assign_material,
VIEW3D_MT_select_material]

def register():
    register = bpy.types.register
    for cls in classes:
        register(cls)

    km = bpy.context.manager.active_keyconfig.keymaps['3D View']
    kmi = km.items.add('wm.call_menu', 'Q', 'PRESS')
    kmi.properties.name = "VIEW3D_MT_master_material"

def unregister():
    unregister = bpy.types.unregister
    for cls in classes:
        unregister(cls)

    km = bpy.context.manager.active_keyconfig.keymaps['3D View']
    for kmi in km.items:
        if kmi.idname == 'wm.call_menu':
            if kmi.properties.name ==  "VIEW3D_MT_master_material":
                km.remove_item(kmi)
                break

if __name__ == "__main__":
    register()