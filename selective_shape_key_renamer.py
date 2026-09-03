bl_info = {
    "name": "Selective Shape Key Renamer",
    "author": "Faiber",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Tool",
    "description": "Renombra de forma selectiva las shape keys añadiendo prefijos y sufijos.",
    "warning": "",
    "doc_url": "",
    "category": "Object",
}

import bpy

def update_use_prefix(self, context):
    if self.sskr_use_prefix:
        self.sskr_use_suffix = False

def update_use_suffix(self, context):
    if self.sskr_use_suffix:
        self.sskr_use_prefix = False

# 1. PropertyGroup para los elementos de la lista (Shape Key individual)
class SSKR_ShapeKeyItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name")
    is_selected: bpy.props.BoolProperty(
        name="Selected", 
        default=False, 
        description="Seleccionar para renombrar"
    )

# 2. Operador para cargar las shape keys del objeto activo
class SSKR_OT_LoadShapeKeys(bpy.types.Operator):
    bl_idname = "object.sskr_load_shape_keys"
    bl_label = "Cargar Shape Keys"
    bl_description = "Cargar todas las shape keys del objeto activo (ignora 'Basis')"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        scene = context.scene
        
        # Limpiar la lista actual
        scene.sskr_shape_keys.clear()
        
        if obj and obj.type == 'MESH' and obj.data.shape_keys:
            loaded_count = 0
            for kb in obj.data.shape_keys.key_blocks:
                if kb.name != "Basis":
                    item = scene.sskr_shape_keys.add()
                    item.name = kb.name
                    item.is_selected = False
                    loaded_count += 1
            self.report({'INFO'}, f"Se han cargado {loaded_count} shape keys.")
        else:
            self.report({'WARNING'}, "El objeto activo no es una malla o no tiene shape keys.")
            
        return {'FINISHED'}

# 3. Operadores de Selección Masiva (Seleccionar Todas / Desmarcar Todas)
class SSKR_OT_SelectAll(bpy.types.Operator):
    bl_idname = "object.sskr_select_all"
    bl_label = "Seleccionar Todas"
    bl_description = "Marca todas las shape keys en la lista"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for item in context.scene.sskr_shape_keys:
            item.is_selected = True
        return {'FINISHED'}

class SSKR_OT_DeselectAll(bpy.types.Operator):
    bl_idname = "object.sskr_deselect_all"
    bl_label = "Desmarcar Todas"
    bl_description = "Desmarca todas las shape keys en la lista"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for item in context.scene.sskr_shape_keys:
            item.is_selected = False
        return {'FINISHED'}

# 4. Operador para Aplicar Renombrado
class SSKR_OT_ApplyRename(bpy.types.Operator):
    bl_idname = "object.sskr_apply_rename"
    bl_label = "Aplicar a Seleccionadas"
    bl_description = "Añade el prefijo y/o sufijo a las shape keys seleccionadas"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        scene = context.scene
        
        prefix = scene.sskr_prefix if scene.sskr_use_prefix else ""
        suffix = scene.sskr_suffix if scene.sskr_use_suffix else ""
        
        if not obj or obj.type != 'MESH' or not obj.data.shape_keys:
            self.report({'WARNING'}, "El objeto actual no es válido o perdió sus shape keys.")
            return {'CANCELLED'}
            
        key_blocks = obj.data.shape_keys.key_blocks
        renamed_count = 0
        
        # Iterar únicamente sobre los elementos que tienen el checkbox marcado
        for item in scene.sskr_shape_keys:
            if item.is_selected:
                if item.name in key_blocks:
                    kb = key_blocks[item.name]
                    new_name = kb.name
                    
                    # Validación condicional: Evitar duplicar prefijo
                    if prefix and not new_name.startswith(prefix):
                        new_name = prefix + new_name
                    
                    # Validación condicional: Evitar duplicar sufijo
                    if suffix and not new_name.endswith(suffix):
                        new_name = new_name + suffix
                    
                    # Si el nombre cambió, actualizarlo en el objeto y en la lista
                    if new_name != kb.name:
                        kb.name = new_name
                        item.name = new_name
                        renamed_count += 1
                        
        self.report({'INFO'}, f"Shape keys renombradas exitosamente: {renamed_count}")
        return {'FINISHED'}

# 5. Interfaz de Usuario (Panel N)
class SSKR_PT_Panel(bpy.types.Panel):
    bl_label = "Selective Shape Key Renamer"
    bl_idname = "SSKR_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Campos de texto para Prefijo y Sufijo
        col = layout.column(align=True)
        
        row_pref = col.row(align=True)
        row_pref_text = row_pref.row(align=True)
        row_pref_text.active = scene.sskr_use_prefix
        row_pref_text.prop(scene, "sskr_prefix", text="Prefijo")
        row_pref.prop(scene, "sskr_use_prefix", text="")
        
        row_suf = col.row(align=True)
        row_suf_text = row_suf.row(align=True)
        row_suf_text.active = scene.sskr_use_suffix
        row_suf_text.prop(scene, "sskr_suffix", text="Sufijo")
        row_suf.prop(scene, "sskr_use_suffix", text="")
        
        layout.separator()
        
        # Botón para cargar shape keys
        layout.operator(SSKR_OT_LoadShapeKeys.bl_idname, icon='FILE_REFRESH')
        
        # Botones de selección masiva
        row = layout.row(align=True)
        row.operator(SSKR_OT_SelectAll.bl_idname)
        row.operator(SSKR_OT_DeselectAll.bl_idname)
        
        layout.separator()
        
        # Lista dinámica de shape keys con checkboxes
        box = layout.box()
        if len(scene.sskr_shape_keys) > 0:
            for item in scene.sskr_shape_keys:
                row = box.row()
                # prop dibuja el checkbox de is_selected con el nombre de la shape key como texto
                row.prop(item, "is_selected", text=item.name)
        else:
            box.label(text="No hay shape keys cargadas", icon='INFO')
            
        layout.separator()
        
        # Botón para aplicar el renombrado a las shape keys con checkbox marcado
        layout.operator(SSKR_OT_ApplyRename.bl_idname, icon='FONT_DATA')

# Lista de clases para registrar
classes = (
    SSKR_ShapeKeyItem,
    SSKR_OT_LoadShapeKeys,
    SSKR_OT_SelectAll,
    SSKR_OT_DeselectAll,
    SSKR_OT_ApplyRename,
    SSKR_PT_Panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    # Registrar propiedades a nivel de Scene
    bpy.types.Scene.sskr_use_prefix = bpy.props.BoolProperty(
        name="Usar Prefijo",
        description="Habilitar el uso de prefijo",
        default=True,
        update=update_use_prefix
    )
    bpy.types.Scene.sskr_use_suffix = bpy.props.BoolProperty(
        name="Usar Sufijo",
        description="Habilitar el uso de sufijo",
        default=False,
        update=update_use_suffix
    )
    bpy.types.Scene.sskr_prefix = bpy.props.StringProperty(
        name="Prefijo",
        description="Prefijo que se añadirá al inicio del nombre de la shape key",
        default=""
    )
    bpy.types.Scene.sskr_suffix = bpy.props.StringProperty(
        name="Sufijo",
        description="Sufijo que se añadirá al final del nombre de la shape key",
        default=""
    )
    # CollectionProperty para la lista temporal de shape keys
    bpy.types.Scene.sskr_shape_keys = bpy.props.CollectionProperty(type=SSKR_ShapeKeyItem)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    # Eliminar propiedades al desregistrar
    del bpy.types.Scene.sskr_use_prefix
    del bpy.types.Scene.sskr_use_suffix
    del bpy.types.Scene.sskr_prefix
    del bpy.types.Scene.sskr_suffix
    del bpy.types.Scene.sskr_shape_keys

if __name__ == "__main__":
    register()
