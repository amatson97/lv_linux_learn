# User Interface Components

The `ui/` module contains all GTK-based user interface components and handlers for the GUI application (menu.py).

## Modules

### handlers.py
**RepositoryActionHandler** - Event handler for repository operations

**Responsibilities:**
- Repository action event handling
- Script execution callbacks
- Error handling and user feedback
- State management

### dialogs.py
**Dialog Factory & Wrappers**

**Key Classes:**
- `DialogFactory` - Factory for creating dialogs
- `StandardDialogs` - Standard dialog types

**Supported Dialogs:**
- Error dialogs
- Warning dialogs
- Info dialogs
- Confirmation dialogs
- Input dialogs

### dialog_helpers.py
**Basic GTK Dialog Utilities**

**Functions:**
- Basic dialog creation
- Text input dialogs
- Simple selection dialogs

### dialog_helpers_extended.py
**Extended Dialog Utilities**

**Functions:**
- Advanced dialogs
- Custom layouts
- Complex user interactions

### ui_components.py
**GTK Widget Components**

**Components:**
- Filtered treeviews
- Custom list views
- Progress displays
- Status indicators

### Tab Handlers

#### repository_tab.py
**RepositoryTabHandler** - Main repository management tab

**Features:**
- Repository selection
- Script browsing
- Script execution
- Update management

#### local_repository_tab.py
**LocalRepositoryTabHandler** - Local script management

**Features:**
- Cached script management
- Script removal
- Local execution
- Batch operations

#### custom_manifest_tab.py
**CustomManifestTabHandler** - Custom repository configuration

**Features:**
- Add custom repositories
- Manifest configuration
- Repository testing
- Settings management

## Dependencies

```
handlers.py
  └─ dialogs.py

dialogs.py
  ├─ dialog_helpers.py
  └─ dialog_helpers_extended.py

ui_components.py
  └─ (minimal dependencies)

repository_tab.py
  ├─ handlers.py
  ├─ ui_components.py
  └─ (core modules)

local_repository_tab.py
  ├─ handlers.py
  ├─ ui_components.py
  └─ (utilities)

custom_manifest_tab.py
  ├─ handlers.py
  ├─ dialogs.py
  └─ (utilities)
```

## Usage

### Creating Dialogs

```python
from lib.ui.dialogs import DialogFactory

factory = DialogFactory()
factory.show_info("Title", "Message")
factory.show_error("Error", "Error message")
result = factory.show_confirmation("Confirm?", "Are you sure?")
```

### Using Tab Handlers

```python
from lib.ui.repository_tab import RepositoryTabHandler

handler = RepositoryTabHandler(window, callbacks)
tab_widget = handler.create_tab()
```

### Custom UI Components

```python
from lib.ui.ui_components import create_filtered_treeview

treeview = create_filtered_treeview(data, columns)
```

## GTK Requirements

- PyGObject with GTK3 bindings
- Pango for text rendering
- GdkPixbuf for image handling

## Testing

UI components are tested with:
- Unit tests in `tests/unit/`
- Integration tests in `tests/integration/`
- Mock GTK components for headless testing

## Related Modules

- **../core/** - Business logic
- **../utilities/** - Helper utilities
- **../../menu.py** - Main GUI application
- **../../tests/** - Test suite
