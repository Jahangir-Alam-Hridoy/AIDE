#!/usr/bin/env python3
import sys
import re
from pathlib import Path

# ======================================
# Core imports for Jetpack Compose + Kotlin
# ======================================
IMPORT_MAP = {
    # ===============================
    # Layout (foundation.layout)
    # ===============================
    "Column": "import androidx.compose.foundation.layout.Column",
    "Row": "import androidx.compose.foundation.layout.Row",
    "Box": "import androidx.compose.foundation.layout.Box",
    "Spacer": "import androidx.compose.foundation.layout.Spacer",
    "fillMaxSize": "import androidx.compose.foundation.layout.fillMaxSize",
    "fillMaxWidth": "import androidx.compose.foundation.layout.fillMaxWidth",
    "fillMaxHeight": "import androidx.compose.foundation.layout.fillMaxHeight",
    "wrapContentSize": "import androidx.compose.foundation.layout.wrapContentSize",
    "padding": "import androidx.compose.foundation.layout.padding",
    "size": "import androidx.compose.foundation.layout.size",
    "width": "import androidx.compose.foundation.layout.width",
    "height": "import androidx.compose.foundation.layout.height",
    "background": "import androidx.compose.foundation.background",
    "weight": "import androidx.compose.foundation.layout.weight",
    "AspectRatio": "import androidx.compose.foundation.layout.aspectRatio",
    "FlowRow": "import androidx.compose.foundation.layout.FlowRow",
    "FlowColumn": "import androidx.compose.foundation.layout.FlowColumn",

    # ===============================
    # Foundation (basic widgets)
    # ===============================
    "Image": "import androidx.compose.foundation.Image",
    "BasicText": "import androidx.compose.foundation.text.BasicText",
    "BasicTextField": "import androidx.compose.foundation.text.BasicTextField",
    "ClickableText": "import androidx.compose.foundation.text.ClickableText",
    "LazyColumn": "import androidx.compose.foundation.lazy.LazyColumn",
    "LazyRow": "import androidx.compose.foundation.lazy.LazyRow",
    "items": "import androidx.compose.foundation.lazy.items",
    "itemsIndexed": "import androidx.compose.foundation.lazy.itemsIndexed",
    "rememberLazyListState": "import androidx.compose.foundation.lazy.rememberLazyListState",
    "verticalScroll": "import androidx.compose.foundation.verticalScroll",
    "horizontalScroll": "import androidx.compose.foundation.horizontalScroll",
    "rememberScrollState": "import androidx.compose.foundation.rememberScrollState",
    "BorderStroke": "import androidx.compose.foundation.BorderStroke",

    # ===============================
    # Material3
    # ===============================
    "Button": "import androidx.compose.material3.Button",
    "Text": "import androidx.compose.material3.Text",
    "Surface": "import androidx.compose.material3.Surface",
    "MaterialTheme": "import androidx.compose.material3.MaterialTheme",
    "OutlinedTextField": "import androidx.compose.material3.OutlinedTextField",
    "TextField": "import androidx.compose.material3.TextField",
    "Scaffold": "import androidx.compose.material3.Scaffold",
    "TopAppBar": "import androidx.compose.material3.TopAppBar",
    "Card": "import androidx.compose.material3.Card",
    "AlertDialog": "import androidx.compose.material3.AlertDialog",
    "Checkbox": "import androidx.compose.material3.Checkbox",
    "Switch": "import androidx.compose.material3.Switch",
    "RadioButton": "import androidx.compose.material3.RadioButton",
    "Slider": "import androidx.compose.material3.Slider",
    "LinearProgressIndicator": "import androidx.compose.material3.LinearProgressIndicator",
    "CircularProgressIndicator": "import androidx.compose.material3.CircularProgressIndicator",
    "FloatingActionButton": "import androidx.compose.material3.FloatingActionButton",
    "Icon": "import androidx.compose.material3.Icon",
    "IconButton": "import androidx.compose.material3.IconButton",
    "DropdownMenu": "import androidx.compose.material3.DropdownMenu",
    "DropdownMenuItem": "import androidx.compose.material3.DropdownMenuItem",
    "SnackbarHost": "import androidx.compose.material3.SnackbarHost",
    "SnackbarHostState": "import androidx.compose.material3.SnackbarHostState",

    # ===============================
    # Runtime
    # ===============================
    "Composable": "import androidx.compose.runtime.Composable",
    "remember": "import androidx.compose.runtime.remember",
    "mutableStateOf": "import androidx.compose.runtime.mutableStateOf",
    "mutableIntStateOf": "import androidx.compose.runtime.mutableIntStateOf",
    "mutableLongStateOf": "import androidx.compose.runtime.mutableLongStateOf",
    "mutableFloatStateOf": "import androidx.compose.runtime.mutableFloatStateOf",
    "LaunchedEffect": "import androidx.compose.runtime.LaunchedEffect",
    "SideEffect": "import androidx.compose.runtime.SideEffect",
    "DisposableEffect": "import androidx.compose.runtime.DisposableEffect",
    "rememberCoroutineScope": "import androidx.compose.runtime.rememberCoroutineScope",
    "getValue": "import androidx.compose.runtime.getValue",
    "setValue": "import androidx.compose.runtime.setValue",
    "rememberSaveable": "import androidx.compose.runtime.saveable.rememberSaveable",
    "produceState": "import androidx.compose.runtime.produceState",
    "derivedStateOf": "import androidx.compose.runtime.derivedStateOf",

    # ===============================
    # UI Core
    # ===============================
    "Modifier": "import androidx.compose.ui.Modifier",
    "Alignment": "import androidx.compose.ui.Alignment",
    "Color": "import androidx.compose.ui.graphics.Color",
    "Brush": "import androidx.compose.ui.graphics.Brush",
    "Shape": "import androidx.compose.ui.graphics.Shape",
    "CircleShape": "import androidx.compose.foundation.shape.CircleShape",
    "RoundedCornerShape": "import androidx.compose.foundation.shape.RoundedCornerShape",
    "sp": "import androidx.compose.ui.unit.sp",
    "dp": "import androidx.compose.ui.unit.dp",
    "IntOffset": "import androidx.compose.ui.unit.IntOffset",
    "IntSize": "import androidx.compose.ui.unit.IntSize",

    # ===============================
    # Animation
    # ===============================
    "animateFloatAsState": "import androidx.compose.animation.core.animateFloatAsState",
    "tween": "import androidx.compose.animation.core.tween",
    "spring": "import androidx.compose.animation.core.spring",
    "keyframes": "import androidx.compose.animation.core.keyframes",
    "InfiniteTransition": "import androidx.compose.animation.core.InfiniteTransition",
    "rememberInfiniteTransition": "import androidx.compose.animation.core.rememberInfiniteTransition",

    # ===============================
    # AndroidX / Activity
    # ===============================
    "Bundle": "import android.os.Bundle",
    "ComponentActivity": "import androidx.activity.ComponentActivity",
    "setContent": "import androidx.activity.compose.setContent",
    "Context": "import android.content.Context",
    "Intent": "import android.content.Intent",

    # ===============================
    # Tools
    # ===============================
    "Preview": "import androidx.compose.ui.tooling.preview.Preview",
}
# ======================================
# Detect missing imports
# ======================================
def find_missing_imports(code: str):
    missing = []

    # Remove all comments first to avoid false positives
    # Remove single-line comments
    code_no_comments = re.sub(r'//.*', '', code)
    # Remove block comments
    code_no_comments = re.sub(r'/\*.*?\*/', '', code_no_comments, flags=re.DOTALL)
    
    # Also check for commented imports that need to be uncommented
    commented_imports = []
    code_lines = code.splitlines()
    for line in code_lines:
        stripped = line.strip()
        if stripped.startswith('//import') or stripped.startswith('/*import') or stripped.startswith('* import'):
            # Extract the actual import statement
            import_match = re.search(r'import\s+.*', stripped)
            if import_match:
                import_stmt = import_match.group(0)
                commented_imports.append(import_stmt)
    
    for symbol, import_stmt in IMPORT_MAP.items():
        # More precise matching to avoid false positives
        pattern = rf"(?<!\w){symbol}(?!\w)"
        if re.search(pattern, code_no_comments):
            # Check if import already exists (commented or uncommented)
            import_exists = import_stmt in code
            import_commented = any(import_stmt in commented for commented in commented_imports)
            
            if not import_exists and not import_commented:
                missing.append(import_stmt)
            elif import_commented:
                # This import is commented out, we need to uncomment it
                missing.append(("uncomment", import_stmt))

    # 'by' delegate check
    if " by " in code_no_comments:
        if IMPORT_MAP["getValue"] not in code:
            missing.append(IMPORT_MAP["getValue"])
        if IMPORT_MAP["setValue"] not in code:
            missing.append(IMPORT_MAP["setValue"])

    return missing

# ======================================
# Insert imports smartly
# ======================================
def insert_imports(code_lines, imports):
    if not code_lines:
        return code_lines

    # Find the package statement and insert after it
    package_line_index = -1
    for i, line in enumerate(code_lines):
        if line.strip().startswith("package"):
            package_line_index = i
            break

    if package_line_index == -1:
        # No package statement, insert at top
        before = code_lines[:1] if code_lines else []
        after = code_lines[1:] if len(code_lines) > 1 else []
    else:
        # Insert after package statement
        before = code_lines[:package_line_index+1]
        after = code_lines[package_line_index+1:]

    existing_imports = [line for line in after if line.strip().startswith("import")]
    new_imports = [imp for imp in imports if isinstance(imp, str) and imp not in existing_imports]

    if not new_imports:
        return code_lines

    # Find where imports end and other code begins
    non_import_start = 0
    for i, line in enumerate(after):
        if not line.strip().startswith("import") and line.strip():
            non_import_start = i
            break

    non_import_lines = after[non_import_start:]
    import_lines = after[:non_import_start]

    # Add new imports to existing ones
    all_imports = sorted(set(import_lines + new_imports))
    
    return before + all_imports + non_import_lines

# ======================================
# Apply auto-fix
# ======================================
def apply_auto_fix(file_path, code_lines, missing_imports):
    if not missing_imports:
        return
    
    # Separate regular imports from uncomment operations
    regular_imports = []
    uncomment_imports = []
    
    for imp in missing_imports:
        if isinstance(imp, tuple) and imp[0] == "uncomment":
            uncomment_imports.append(imp[1])
        else:
            regular_imports.append(imp)

    # First uncomment any commented imports
    for i, line in enumerate(code_lines):
        for uncomment_import in uncomment_imports:
            if uncomment_import in line and line.strip().startswith('//'):
                code_lines[i] = line.replace('//', '', 1)
                break

            """
            """
    # Then add new imports
    if regular_imports:
        code_lines = insert_imports(code_lines, regular_imports)

    # Write the file
    try:
        file_path.write_text("\n".join(code_lines), encoding='utf-8')
        print(f"✨ Auto-fix applied on {file_path.name}")
        if regular_imports:
            print(f"   Added imports: {len(regular_imports)}")
        if uncomment_imports:
            print(f"   Uncommented imports: {len(uncomment_imports)}")
    except Exception as e:
        print(f"❌ Error writing file: {e}")

# ======================================
# Main
# ======================================
def main():
    args = sys.argv[1:]
    auto_mode = "--auto" in args
    if auto_mode:
        args.remove("--auto")

    if not args:
        print("Usage: checkimport <file_path> [--auto]")
        return

    file_path = Path(args[0])
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return

    try:
        code = file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return

    # Skip files without @Composable annotations
    if "@Composable" not in code:
        print(f"⏭️ Skipping {file_path.name} (no @Composable found)")
        return
        
    code_lines = code.splitlines()
    missing = find_missing_imports(code)

    if not missing:
        if not auto_mode:
            print("✅ All imports OK. No changes needed.")
        return

    if auto_mode:
        apply_auto_fix(file_path, code_lines, missing)
    else:
        print("🔍 Found missing imports that can be fixed:")
        regular_count = len([imp for imp in missing if not isinstance(imp, tuple)])
        uncomment_count = len([imp for imp in missing if isinstance(imp, tuple)])
        
        if regular_count > 0:
            print(f"   Missing imports: {regular_count}")
        if uncomment_count > 0:
            print(f"   Commented imports to uncomment: {uncomment_count}")
        print("💡 Run with --auto flag to automatically fix these issues")

if __name__ == "__main__":
    main()
