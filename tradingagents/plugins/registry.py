PLUGIN_REGISTRY = {
    "data_sources": {},
    "analysts": {},
    "strategies": {},
    "traders": {},
    "graph_engine": {}
}

def register_plugin(plugin_type: str, name: str, plugin_class):
    """
    注册插件到全局注册表
    
    参数:
        plugin_type: 插件类型 ('data_sources', 'analysts', 'strategies', 'traders', 'graph_engine')
        name: 插件唯一标识名
        plugin_class: 插件类
    """
    if plugin_type not in PLUGIN_REGISTRY:
        PLUGIN_REGISTRY[plugin_type] = {}
    
    PLUGIN_REGISTRY[plugin_type][name] = plugin_class

def get_plugin(plugin_type: str, name: str):
    """
    从注册表获取插件类
    
    参数:
        plugin_type: 插件类型
        name: 插件名称
    
    返回:
        插件类
    """
    if plugin_type not in PLUGIN_REGISTRY:
        raise ValueError(f"无效的插件类型: {plugin_type}")
    
    if name not in PLUGIN_REGISTRY[plugin_type]:
        raise ValueError(f"{plugin_type} 中未找到插件: {name}")
    
    return PLUGIN_REGISTRY[plugin_type][name]

def list_plugins(plugin_type: str = None):
    """
    列出所有可用插件或指定类型的插件
    
    参数:
        plugin_type: 可选，指定插件类型
    
    返回:
        插件字典 {插件类型: {插件名: 插件类}}
    """
    if plugin_type:
        if plugin_type not in PLUGIN_REGISTRY:
            raise ValueError(f"无效的插件类型: {plugin_type}")
        return {plugin_type: PLUGIN_REGISTRY[plugin_type]}
    return PLUGIN_REGISTRY
