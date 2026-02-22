"""Tree-sitter parser"""

import tree_sitter
import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Tree, Node
from typing import Optional, List, Dict, Tuple
from pathlib import Path

from codemind.core.logger import logger
from codemind.parser.models.symbol import Symbol, FunctionSymbol, ClassSymbol, ImportSymbol, SymbolType

class TreeSitterParser:
    """Tree-sitter parser"""
    
    def __init__(self):
        """Initialize Tree-sitter parser"""
        self.language = Language(tspython.language())
        self.parser = Parser(self.language)
        self._init_queries()
    
    def _init_queries(self):
        """Initialize Tree-sitter queries"""
        # Function definition query
        self.function_query = self.language.query("""
            (function_definition
                name: (identifier) @func_name
                parameters: (parameters) @params
                body: (block) @body
            ) @func_def
            
            (decorated_definition
                (decorator)* @decorators
                definition: (function_definition
                    name: (identifier) @func_name
                    parameters: (parameters) @params
                    return_type: (type)? @return_type
                    body: (block) @body
                ) @func_def
            )
        """)
        
        # Class definition query
        self.class_query = self.language.query("""
            (class_definition
                name: (identifier) @class_name
                superclasses: (argument_list)? @bases
                body: (block) @body
            ) @class_def
        """)
        
        # Import query
        self.import_query = self.language.query("""
            (import_statement
                name: (dotted_name) @module_name
            ) @import
            
            (import_from_statement
                module_name: (dotted_name)? @module
                name: (dotted_name) @name
            ) @from_import
        """)
        
        # Function call query
        self.call_query = self.language.query("""
            (call
                function: [
                    (identifier) @func_name
                    (attribute
                        object: (identifier) @obj
                        attribute: (identifier) @method
                    )
                ]
            ) @call
        """)
    
    def parse(self, source_code: bytes, file_path: str) -> Optional[Tree]:
        """Parse source code"""
        try:
            tree = self.parser.parse(source_code)
            return tree
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return None
    
    def parse_file(self, file_path: str) -> Optional[Tree]:
        """Parse file"""
        try:
            with open(file_path, 'rb') as f:
                source_code = f.read()
            return self.parse(source_code, file_path)
        except Exception as e:
            logger.error(f"Failed to parse file {file_path}: {e}")
            return None
    
    def extract_symbols(self, tree: Tree, source_code: bytes, 
                       file_path: str) -> List[Symbol]:
        """Extract symbols from AST"""
        symbols = []
        
        # Extract module symbol
        module_symbol = self._create_module_symbol(file_path, source_code)
        symbols.append(module_symbol)
        
        try:
            # Traverse AST directly to extract symbols
            self._traverse_ast(tree.root_node, source_code, file_path, module_symbol.id, symbols)
        except Exception as e:
            logger.error(f"Failed to extract symbols: {e}")
        
        return symbols
    
    def _traverse_ast(self, node: Node, source_code: bytes, 
                      file_path: str, parent_id: str, 
                      symbols: List[Symbol]) -> None:
        """Traverse AST to extract symbols"""
        # Check for class definition
        if node.type == 'class_definition':
            class_symbol = self._parse_class_node(node, source_code, file_path, parent_id)
            if class_symbol:
                symbols.append(class_symbol)
                # Traverse class body for methods
                body_node = None
                for child in node.children:
                    if child.type == 'block':
                        body_node = child
                        break
                if body_node:
                    for child in body_node.children:
                        self._traverse_ast(child, source_code, file_path, class_symbol.id, symbols)
        # Check for function definition
        elif node.type == 'function_definition':
            function_symbol = self._parse_function_node(node, source_code, file_path, parent_id)
            if function_symbol:
                symbols.append(function_symbol)
        # Check for decorated function
        elif node.type == 'decorated_definition':
            for child in node.children:
                if child.type == 'function_definition':
                    function_symbol = self._parse_function_node(child, source_code, file_path, parent_id)
                    if function_symbol:
                        # Add decorators
                        decorators = []
                        for dec_node in node.children:
                            if dec_node.type == 'decorator':
                                dec_text = source_code[dec_node.start_byte:dec_node.end_byte].decode('utf-8')
                                decorators.append(dec_text)
                        function_symbol.decorators = decorators
                        symbols.append(function_symbol)
                    break
        # Check for import statement
        elif node.type == 'import_statement':
            import_symbol = self._parse_import_node(node, source_code, file_path)
            if import_symbol:
                symbols.append(import_symbol)
        # Check for from import statement
        elif node.type == 'import_from_statement':
            import_symbol = self._parse_import_node(node, source_code, file_path)
            if import_symbol:
                symbols.append(import_symbol)
        
        # Traverse children
        for child in node.children:
            if child.type not in ['block', 'statement', 'expression_statement']:
                self._traverse_ast(child, source_code, file_path, parent_id, symbols)
    
    def _parse_class_node(self, node: Node, source_code: bytes, 
                         file_path: str, parent_id: str) -> Optional[ClassSymbol]:
        """Parse class definition from node"""
        name_node = None
        bases_node = None
        body_node = None
        
        for child in node.children:
            if child.type == 'identifier' and not name_node:
                name_node = child
            elif child.type == 'argument_list':
                bases_node = child
            elif child.type == 'block':
                body_node = child
        
        if not name_node:
            return None
        
        name = source_code[name_node.start_byte:name_node.end_byte].decode('utf-8')
        
        # Extract bases
        bases = []
        if bases_node:
            bases = self._extract_bases(bases_node, source_code)
        
        # Extract class body
        methods = []
        attributes = []
        if body_node:
            for child in body_node.children:
                if child.type == 'function_definition':
                    # Extract method name
                    for func_child in child.children:
                        if func_child.type == 'identifier':
                            method_name = source_code[func_child.start_byte:func_child.end_byte].decode('utf-8')
                            methods.append(method_name)
                            break
                elif child.type == 'expression_statement':
                    expr = child.children[0]
                    if expr.type == 'assignment':
                        attr_node = expr.children[0]
                        if attr_node.type == 'identifier':
                            attr_name = source_code[attr_node.start_byte:attr_node.end_byte].decode('utf-8')
                            attributes.append(attr_name)
        
        # Extract docstring
        docstring = self._extract_docstring(body_node, source_code)
        
        return ClassSymbol(
            id=f"cls_{file_path.replace('/', '_')}_{name}_{node.start_point[0]}",
            name=name,
            type=SymbolType.CLASS,
            file_path=file_path,
            absolute_path=file_path,
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            column_start=node.start_point[1],
            column_end=node.end_point[1],
            source_code=source_code[node.start_byte:node.end_byte].decode('utf-8'),
            docstring=docstring,
            parent_id=parent_id,
            bases=bases,
            methods=methods,
            attributes=attributes
        )
    
    def _parse_function_node(self, node: Node, source_code: bytes, 
                            file_path: str, parent_id: str) -> Optional[FunctionSymbol]:
        """Parse function definition from node"""
        name_node = None
        params_node = None
        return_type_node = None
        body_node = None
        
        for child in node.children:
            if child.type == 'identifier' and not name_node:
                name_node = child
            elif child.type == 'parameters':
                params_node = child
            elif child.type == 'type':
                return_type_node = child
            elif child.type == 'block':
                body_node = child
        
        if not name_node:
            return None
        
        name = source_code[name_node.start_byte:name_node.end_byte].decode('utf-8')
        
        # Extract parameters
        parameters = []
        if params_node:
            parameters = self._extract_parameters(params_node, source_code)
        
        # Extract return type
        return_type = None
        if return_type_node:
            return_type = source_code[return_type_node.start_byte:return_type_node.end_byte].decode('utf-8')
        
        # Extract calls
        calls = []
        if body_node:
            calls = self._extract_calls_from_node(body_node, source_code)
        
        # Check if async
        is_async = b'async' in source_code[node.start_byte:node.start_byte+10]
        
        # Extract docstring
        docstring = self._extract_docstring(body_node, source_code)
        
        return FunctionSymbol(
            id=f"func_{file_path.replace('/', '_')}_{name}_{node.start_point[0]}",
            name=name,
            type=SymbolType.FUNCTION,
            file_path=file_path,
            absolute_path=file_path,
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            column_start=node.start_point[1],
            column_end=node.end_point[1],
            source_code=source_code[node.start_byte:node.end_byte].decode('utf-8'),
            docstring=docstring,
            parent_id=parent_id,
            parameters=parameters,
            return_type=return_type,
            is_async=is_async,
            decorators=[],
            calls=calls
        )
    
    def _parse_import_node(self, node: Node, source_code: bytes, 
                          file_path: str) -> Optional[ImportSymbol]:
        """Parse import statement from node"""
        module_path = ""
        imported_names = []
        is_from_import = node.type == 'import_from_statement'
        is_relative = False
        
        if node.type == 'import_statement':
            for child in node.children:
                if child.type == 'dotted_name':
                    module_path = source_code[child.start_byte:child.end_byte].decode('utf-8')
                    imported_names = [module_path.split('.')[-1]]
                    break
        elif node.type == 'import_from_statement':
            module_node = None
            name_node = None
            for child in node.children:
                if child.type == 'dotted_name' and not module_node:
                    module_node = child
                elif child.type == 'dotted_name' and module_node:
                    name_node = child
            if module_node:
                module_path = source_code[module_node.start_byte:module_node.end_byte].decode('utf-8')
            if name_node:
                name = source_code[name_node.start_byte:name_node.end_byte].decode('utf-8')
                imported_names = [name]
        
        if not module_path and not imported_names:
            return None
        
        return ImportSymbol(
            id=f"imp_{file_path.replace('/', '_')}_{node.start_point[0]}",
            name=module_path or "unknown",
            type=SymbolType.IMPORT,
            file_path=file_path,
            absolute_path=file_path,
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            source_code=source_code[node.start_byte:node.end_byte].decode('utf-8'),
            module_path=module_path,
            imported_names=imported_names,
            is_from_import=is_from_import,
            is_relative=is_relative
        )
    
    def _extract_calls_from_node(self, node: Node, source_code: bytes) -> List[str]:
        """Extract function calls from node"""
        calls = []
        
        if node.type == 'call':
            function_node = node.children[0]
            if function_node.type == 'identifier':
                name = source_code[function_node.start_byte:function_node.end_byte].decode('utf-8')
                calls.append(name)
            elif function_node.type == 'attribute':
                obj_node = function_node.children[0]
                attr_node = function_node.children[1]
                if obj_node.type == 'identifier' and attr_node.type == 'identifier':
                    obj = source_code[obj_node.start_byte:obj_node.end_byte].decode('utf-8')
                    attr = source_code[attr_node.start_byte:attr_node.end_byte].decode('utf-8')
                    calls.append(f"{obj}.{attr}")
        
        # Traverse children
        for child in node.children:
            calls.extend(self._extract_calls_from_node(child, source_code))
        
        return calls
    
    def _create_module_symbol(self, file_path: str, source_code: bytes) -> Symbol:
        """Create module symbol"""
        lines = source_code.decode('utf-8', errors='ignore').split('\n')
        return Symbol(
            id=f"mod_{file_path.replace('/', '_')}",
            name=Path(file_path).stem,
            type=SymbolType.MODULE,
            file_path=file_path,
            absolute_path=file_path,
            line_start=1,
            line_end=len(lines),
            source_code=source_code.decode('utf-8', errors='ignore'),
            docstring=self._extract_module_docstring(lines)
        )
    
    def _parse_class(self, match: Dict[str, List[Node]], source_code: bytes, 
                    file_path: str, parent_id: str) -> Optional[ClassSymbol]:
        """Parse class definition"""
        class_node = match.get('class_def', [None])[0]
        name_node = match.get('class_name', [None])[0]
        
        if not class_node or not name_node:
            return None
        
        name = source_code[name_node.start_byte:name_node.end_byte].decode('utf-8')
        
        # Extract bases
        bases = []
        if 'bases' in match:
            bases_node = match['bases'][0]
            bases = self._extract_bases(bases_node, source_code)
        
        # Extract class body
        body_node = match['body'][0]
        methods, attributes = self._extract_class_members(body_node, source_code)
        
        # Extract docstring
        docstring = self._extract_docstring(body_node, source_code)
        
        return ClassSymbol(
            id=f"cls_{file_path.replace('/', '_')}_{name}_{class_node.start_point[0]}",
            name=name,
            type=SymbolType.CLASS,
            file_path=file_path,
            absolute_path=file_path,
            line_start=class_node.start_point[0] + 1,
            line_end=class_node.end_point[0] + 1,
            column_start=class_node.start_point[1],
            column_end=class_node.end_point[1],
            source_code=source_code[class_node.start_byte:class_node.end_byte].decode('utf-8'),
            docstring=docstring,
            parent_id=parent_id,
            bases=bases,
            methods=methods,
            attributes=attributes
        )
    
    def _parse_function(self, match: Dict[str, List[Node]], source_code: bytes,
                       file_path: str, parent_id: str) -> Optional[FunctionSymbol]:
        """Parse function definition"""
        func_node = match.get('func_def', [None])[0]
        name_node = match.get('func_name', [None])[0]
        
        if not func_node or not name_node:
            return None
        
        name = source_code[name_node.start_byte:name_node.end_byte].decode('utf-8')
        
        # Extract parameters
        parameters = []
        if 'params' in match:
            params_node = match['params'][0]
            parameters = self._extract_parameters(params_node, source_code)
        
        # Extract return type
        return_type = None
        if 'return_type' in match and match['return_type']:
            ret_node = match['return_type'][0]
            return_type = source_code[ret_node.start_byte:ret_node.end_byte].decode('utf-8')
        
        # Extract decorators
        decorators = []
        if 'decorators' in match:
            for dec_node in match['decorators']:
                dec_text = source_code[dec_node.start_byte:dec_node.end_byte].decode('utf-8')
                decorators.append(dec_text)
        
        # Extract function body
        body_node = match['body'][0]
        
        # Extract calls
        calls = self._extract_calls(body_node, source_code)
        
        # Check if async
        is_async = b'async' in source_code[func_node.start_byte:func_node.start_byte+10]
        
        # Extract docstring
        docstring = self._extract_docstring(body_node, source_code)
        
        return FunctionSymbol(
            id=f"func_{file_path.replace('/', '_')}_{name}_{func_node.start_point[0]}",
            name=name,
            type=SymbolType.FUNCTION,
            file_path=file_path,
            absolute_path=file_path,
            line_start=func_node.start_point[0] + 1,
            line_end=func_node.end_point[0] + 1,
            column_start=func_node.start_point[1],
            column_end=func_node.end_point[1],
            source_code=source_code[func_node.start_byte:func_node.end_byte].decode('utf-8'),
            docstring=docstring,
            parent_id=parent_id,
            parameters=parameters,
            return_type=return_type,
            is_async=is_async,
            decorators=decorators,
            calls=calls
        )
    
    def _parse_import(self, match: Dict[str, List[Node]], source_code: bytes,
                     file_path: str) -> Optional[ImportSymbol]:
        """Parse import statement"""
        # Find import node
        import_node = None
        if 'import' in match:
            import_node = match['import'][0]
        elif 'from_import' in match:
            import_node = match['from_import'][0]
        
        if not import_node:
            return None
        
        module_path = ""
        imported_names = []
        
        if 'module_name' in match:
            module_node = match['module_name'][0]
            module_path = source_code[module_node.start_byte:module_node.end_byte].decode('utf-8')
            imported_names = [module_path.split('.')[-1]]
        elif 'module' in match and match['module']:
            module_node = match['module'][0]
            module_path = source_code[module_node.start_byte:module_node.end_byte].decode('utf-8')
            if 'name' in match:
                name_node = match['name'][0]
                name = source_code[name_node.start_byte:name_node.end_byte].decode('utf-8')
                imported_names = [name]
        
        is_from_import = 'from_import' in match
        is_relative = False
        
        return ImportSymbol(
            id=f"imp_{file_path.replace('/', '_')}_{import_node.start_point[0]}",
            name=module_path or "unknown",
            type=SymbolType.IMPORT,
            file_path=file_path,
            absolute_path=file_path,
            line_start=import_node.start_point[0] + 1,
            line_end=import_node.end_point[0] + 1,
            source_code=source_code[import_node.start_byte:import_node.end_byte].decode('utf-8'),
            module_path=module_path,
            imported_names=imported_names,
            is_from_import=is_from_import,
            is_relative=is_relative
        )
    
    def _extract_calls(self, node: Node, source_code: bytes) -> List[str]:
        """Extract function calls"""
        calls = []
        call_captures = self.call_query.captures(node)
        
        for match in self._group_captures(call_captures):
            if 'func_name' in match:
                name_node = match['func_name'][0]
                name = source_code[name_node.start_byte:name_node.end_byte].decode('utf-8')
                calls.append(name)
            elif 'method' in match:
                obj_node = match['obj'][0]
                method_node = match['method'][0]
                obj = source_code[obj_node.start_byte:obj_node.end_byte].decode('utf-8')
                method = source_code[method_node.start_byte:method_node.end_byte].decode('utf-8')
                calls.append(f"{obj}.{method}")
        
        return calls
    
    def _extract_docstring(self, node: Node, source_code: bytes) -> Optional[str]:
        """Extract docstring"""
        for child in node.children:
            if child.type == 'expression_statement':
                expr = child.children[0]
                if expr.type == 'string':
                    return source_code[expr.start_byte:expr.end_byte].decode('utf-8').strip('\"\'')
        return None
    
    def _extract_module_docstring(self, lines: List[str]) -> Optional[str]:
        """Extract module docstring"""
        if lines and lines[0].strip().startswith('"""'):
            docstring = []
            in_docstring = True
            for line in lines:
                docstring.append(line)
                if line.strip().endswith('"""') and len(docstring) > 1:
                    break
            return '\n'.join(docstring).strip('"""').strip()
        return None
    
    def _extract_bases(self, node: Node, source_code: bytes) -> List[str]:
        """Extract class bases"""
        bases = []
        for child in node.children:
            if child.type == 'identifier':
                bases.append(source_code[child.start_byte:child.end_byte].decode('utf-8'))
        return bases
    
    def _extract_parameters(self, node: Node, source_code: bytes) -> List[Dict[str, str]]:
        """Extract function parameters"""
        parameters = []
        for child in node.children:
            if child.type == 'identifier':
                param_name = source_code[child.start_byte:child.end_byte].decode('utf-8')
                parameters.append({'name': param_name, 'type': 'Any'})
        return parameters
    
    def _extract_class_members(self, node: Node, source_code: bytes) -> Tuple[List[str], List[str]]:
        """Extract class members"""
        methods = []
        attributes = []
        
        for child in node.children:
            if child.type == 'function_definition':
                name_node = child.children[1]
                if name_node.type == 'identifier':
                    method_name = source_code[name_node.start_byte:name_node.end_byte].decode('utf-8')
                    methods.append(method_name)
            elif child.type == 'expression_statement':
                expr = child.children[0]
                if expr.type == 'assignment':
                    attr_node = expr.children[0]
                    if attr_node.type == 'identifier':
                        attr_name = source_code[attr_node.start_byte:attr_node.end_byte].decode('utf-8')
                        attributes.append(attr_name)
        
        return methods, attributes
    
    def _group_captures(self, captures: List[Tuple[Node, str]]) -> List[Dict[str, List[Node]]]:
        """Group Tree-sitter captures"""
        groups = []
        current_group = {}
        
        for node, capture_name in captures:
            if capture_name in current_group and capture_name.endswith('_def'):
                groups.append(current_group)
                current_group = {}
            current_group.setdefault(capture_name, []).append(node)
        
        if current_group:
            groups.append(current_group)
        
        return groups