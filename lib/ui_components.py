"""
UI Components Factory - Reusable UI component creation
Provides factory methods for common GTK components used across tab handlers
"""

from gi.repository import Gtk, Pango


class TreeViewFactory:
    """Factory for creating TreeView widgets with common configurations"""
    
    @staticmethod
    def create_standard_tree(columns_config, enable_multiple_selection=False):
        """
        Create a standard TreeView with configured columns
        
        Args:
            columns_config: List of dicts with column config:
                [
                    {"name": "Name", "index": 0, "width": 150, "resizable": True},
                    {"name": "Description", "index": 1, "width": 200, "resizable": True},
                    ...
                ]
            enable_multiple_selection: Allow multiple row selection
            
        Returns:
            (Gtk.TreeView, Gtk.ListStore) tuple
        """
        # Create store based on column count
        store_types = [str] * len(columns_config)
        store = Gtk.ListStore(*store_types)
        
        tree = Gtk.TreeView(model=store)
        tree.set_headers_visible(True)
        
        # Set selection mode
        if enable_multiple_selection:
            tree.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)
        else:
            tree.get_selection().set_mode(Gtk.SelectionMode.SINGLE)
        
        # Add columns
        for col_config in columns_config:
            TreeViewFactory._add_column(tree, col_config)
        
        return tree, store
    
    @staticmethod
    def _add_column(tree, col_config):
        """Add a column to a TreeView"""
        name = col_config.get("name", "Column")
        index = col_config.get("index", 0)
        width = col_config.get("width", 100)
        resizable = col_config.get("resizable", True)
        renderer_type = col_config.get("renderer", "text")
        
        # Create renderer
        if renderer_type == "text":
            renderer = Gtk.CellRendererText()
            ellipsize = col_config.get("ellipsize", False)
            if ellipsize:
                renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        elif renderer_type == "toggle":
            renderer = Gtk.CellRendererToggle()
        else:
            renderer = Gtk.CellRendererText()
        
        # Create column
        column = Gtk.TreeViewColumn(name, renderer)
        
        if renderer_type == "text":
            column.add_attribute(renderer, "text", index)
        elif renderer_type == "toggle":
            column.add_attribute(renderer, "active", index)
        
        column.set_resizable(resizable)
        column.set_min_width(width)
        tree.append_column(column)
    
    @staticmethod
    def create_manifest_tree():
        """Create TreeView for manifest display"""
        columns = [
            {"name": "Name", "index": 0, "width": 150, "resizable": True},
            {"name": "Description", "index": 1, "width": 200, "resizable": True, "ellipsize": True},
            {"name": "Scripts", "index": 2, "width": 60, "resizable": False},
            {"name": "Categories", "index": 3, "width": 100, "resizable": True, "ellipsize": True},
            {"name": "Created", "index": 4, "width": 100, "resizable": False},
        ]
        return TreeViewFactory.create_standard_tree(columns, enable_multiple_selection=True)
    
    @staticmethod
    def create_scripts_tree():
        """Create TreeView for scripts display"""
        columns = [
            {"name": "Script", "index": 0, "width": 250, "resizable": True},
            {"name": "Status", "index": 1, "width": 80, "resizable": False},
            {"name": "Source", "index": 2, "width": 150, "resizable": True},
        ]
        return TreeViewFactory.create_standard_tree(columns, enable_multiple_selection=True)
    
    @staticmethod
    def create_directory_tree():
        """Create TreeView for directory listing"""
        columns = [
            {"name": "Directory Path", "index": 0, "width": 400, "resizable": True},
        ]
        return TreeViewFactory.create_standard_tree(columns, enable_multiple_selection=False)


class ButtonFactory:
    """Factory for creating buttons with standard styling"""
    
    @staticmethod
    def create_button(label, style_class=None, tooltip=""):
        """
        Create a standard button
        
        Args:
            label: Button label text
            style_class: GTK style class (e.g., "suggested-action", "destructive-action")
            tooltip: Tooltip text
            
        Returns:
            Gtk.Button
        """
        button = Gtk.Button(label=label)
        if style_class:
            button.get_style_context().add_class(style_class)
        if tooltip:
            button.set_tooltip_text(tooltip)
        return button
    
    @staticmethod
    def create_action_button(label, tooltip=""):
        """Create a primary action button (blue)"""
        return ButtonFactory.create_button(label, "suggested-action", tooltip)
    
    @staticmethod
    def create_destructive_button(label, tooltip=""):
        """Create a destructive action button (red)"""
        return ButtonFactory.create_button(label, "destructive-action", tooltip)
    
    @staticmethod
    def create_normal_button(label, tooltip=""):
        """Create a normal button (gray)"""
        return ButtonFactory.create_button(label, None, tooltip)
    
    @staticmethod
    def create_button_box(buttons_config, orientation=Gtk.Orientation.HORIZONTAL):
        """
        Create a button box with multiple buttons
        
        Args:
            buttons_config: List of dicts:
                [
                    {"label": "Add", "style": "suggested-action", "callback": handler},
                    {"label": "Delete", "style": "destructive-action", "callback": handler},
                    ...
                ]
            orientation: Gtk.Orientation.HORIZONTAL or VERTICAL
            
        Returns:
            (Gtk.Box, buttons_dict) tuple where buttons_dict maps labels to buttons
        """
        box = Gtk.Box(orientation=orientation, spacing=5)
        buttons = {}
        
        for config in buttons_config:
            label = config.get("label", "Button")
            style = config.get("style", None)
            callback = config.get("callback")
            
            button = ButtonFactory.create_button(label, style)
            if callback:
                button.connect("clicked", callback)
            
            buttons[label] = button
            box.pack_start(button, False, False, 0)
        
        return box, buttons


class ScrolledContainerFactory:
    """Factory for creating scrollable containers"""
    
    @staticmethod
    def create_scrolled_window(child_widget, h_policy=Gtk.PolicyType.AUTOMATIC,
                               v_policy=Gtk.PolicyType.AUTOMATIC,
                               min_height=200, min_width=None):
        """
        Create a scrolled window container
        
        Args:
            child_widget: Widget to contain (typically TreeView)
            h_policy: Horizontal scrollbar policy
            v_policy: Vertical scrollbar policy
            min_height: Minimum height in pixels
            min_width: Minimum width in pixels (None = no minimum)
            
        Returns:
            Gtk.ScrolledWindow
        """
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(h_policy, v_policy)
        
        if min_height or min_width:
            width = min_width if min_width else -1
            scrolled.set_size_request(width, min_height)
        
        scrolled.add(child_widget)
        return scrolled


class LabelFactory:
    """Factory for creating labels with common configurations"""
    
    @staticmethod
    def create_label(text, markup=False, wrap=True, xalign=0, selectable=False):
        """
        Create a standard label
        
        Args:
            text: Label text
            markup: Whether to use Pango markup
            wrap: Whether to wrap text
            xalign: Horizontal alignment (0=left, 0.5=center, 1=right)
            selectable: Whether text is selectable
            
        Returns:
            Gtk.Label
        """
        label = Gtk.Label()
        
        if markup:
            label.set_markup(text)
        else:
            label.set_text(text)
        
        label.set_line_wrap(wrap)
        label.set_xalign(xalign)
        label.set_selectable(selectable)
        
        return label
    
    @staticmethod
    def create_title_label(text):
        """Create a title/heading label (bold, larger)"""
        label = LabelFactory.create_label(f"<b>{text}</b>", markup=True)
        label.set_line_wrap(True)
        return label
    
    @staticmethod
    def create_info_label(text):
        """Create an info/description label (italic, gray)"""
        label = LabelFactory.create_label(f"<i>{text}</i>", markup=True)
        label.set_line_wrap(True)
        label.set_xalign(0)
        return label
    
    @staticmethod
    def create_error_label(text):
        """Create an error label (red text)"""
        label = LabelFactory.create_label(f"<span color='red'>{text}</span>", markup=True)
        label.set_line_wrap(True)
        return label
    
    @staticmethod
    def create_status_label(text, status="info"):
        """
        Create a status label with color coding
        
        Args:
            text: Label text
            status: "info" (blue), "success" (green), "warning" (orange), "error" (red)
            
        Returns:
            Gtk.Label
        """
        colors = {
            "info": "blue",
            "success": "green",
            "warning": "orange",
            "error": "red"
        }
        color = colors.get(status, "gray")
        label = LabelFactory.create_label(f"<span color='{color}'>{text}</span>", markup=True)
        return label


class NotebookFactory:
    """Factory for creating tabbed notebook containers"""
    
    @staticmethod
    def create_notebook(tabs_config):
        """
        Create a notebook with tabs
        
        Args:
            tabs_config: List of dicts:
                [
                    {"label": "Tab 1", "content": widget, "icon": "📁"},
                    {"label": "Tab 2", "content": widget, "icon": "🌐"},
                    ...
                ]
            
        Returns:
            (Gtk.Notebook, tabs_dict) tuple where tabs_dict maps labels to page indices
        """
        notebook = Gtk.Notebook()
        notebook.set_tab_pos(Gtk.PositionType.TOP)
        
        tabs = {}
        for i, config in enumerate(tabs_config):
            label_text = config.get("label", f"Tab {i}")
            icon = config.get("icon", "")
            content = config.get("content")
            
            if icon:
                label_text = f"{icon} {label_text}"
            
            tab_label = Gtk.Label(label=label_text)
            notebook.append_page(content, tab_label)
            tabs[config.get("label", f"Tab {i}")] = i
        
        return notebook, tabs


class BoxFactory:
    """Factory for creating box containers with standard configurations"""
    
    @staticmethod
    def create_section_box(title="", vertical=True, spacing=10):
        """
        Create a box for a UI section with optional title
        
        Args:
            title: Optional section title
            vertical: True for vertical, False for horizontal
            spacing: Space between children
            
        Returns:
            Gtk.Box or (Gtk.Box, Gtk.Label) if title provided
        """
        orientation = Gtk.Orientation.VERTICAL if vertical else Gtk.Orientation.HORIZONTAL
        box = Gtk.Box(orientation=orientation, spacing=spacing)
        box.set_margin_start(10)
        box.set_margin_end(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        
        if title:
            title_label = LabelFactory.create_title_label(title)
            return box, title_label
        
        return box
    
    @staticmethod
    def create_control_box(buttons_config):
        """
        Create a control/toolbar box with buttons
        
        Args:
            buttons_config: List of button config dicts (see ButtonFactory.create_button_box)
            
        Returns:
            Gtk.Box with buttons
        """
        box, _ = BoxFactory.create_section_box(vertical=False, spacing=5)
        button_box, _ = ButtonFactory.create_button_box(buttons_config)
        
        # Replace the margin setup for control boxes
        button_box.set_margin_start(0)
        button_box.set_margin_end(0)
        button_box.set_margin_top(0)
        button_box.set_margin_bottom(0)
        
        return button_box


# ============================================================================
# FILTERED TREEVIEW HELPERS
# ============================================================================

def create_filtered_treeview(column_types, column_configs, filter_func=None):
    """
    Create a TreeView with filtering support (simplified interface)
    
    Eliminates the repetitive pattern of creating ListStore -> TreeModelFilter -> TreeView.
    
    Args:
        column_types: List of GObject types (e.g., [str, str, str, bool, str])
        column_configs: List of column config dicts (see TreeViewFactory.create_standard_tree)
        filter_func: Optional filter function(model, iter, user_data) -> bool
    
    Returns:
        (tree, store, filter_model) tuple where:
            tree: Gtk.TreeView ready for display
            store: Gtk.ListStore (populate this with data)
            filter_model: Gtk.TreeModelFilter (refilter when search changes)
    
    Example:
        tree, store, filter_model = create_filtered_treeview(
            column_types=[str, str, str],
            column_configs=[
                {"name": "Name", "index": 0, "width": 200},
                {"name": "Description", "index": 1, "width": 300},
                {"name": "Category", "index": 2, "width": 150}
            ],
            filter_func=my_search_filter_func
        )
        
        # Populate
        store.append(["script1", "Does something", "tools"])
        
        # Refilter when search changes
        filter_model.refilter()
    """
    # Create store
    store = Gtk.ListStore(*column_types)
    
    # Create filter (if filter_func provided)
    if filter_func:
        filter_model = store.filter_new()
        filter_model.set_visible_func(filter_func)
        tree_model = filter_model
    else:
        filter_model = None
        tree_model = store
    
    # Create TreeView
    tree = Gtk.TreeView(model=tree_model)
    tree.set_headers_visible(True)
    tree.get_selection().set_mode(Gtk.SelectionMode.SINGLE)
    
    # Add columns
    for col_config in column_configs:
        TreeViewFactory._add_column(tree, col_config)
    
    return tree, store, filter_model

