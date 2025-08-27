#!/usr/bin/env python3
"""
Migration Script for LLMgine-MCP Integration

This script helps migrate existing LLMgine projects to use the new MCP-based
ToolManager system. It provides automated migration, validation, and rollback
capabilities.
"""

import argparse
import asyncio
import json
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from llmgine.llm.tools import ToolManager, create_mcp_tool_manager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LLMgineMCPMigrator:
    """
    Automated migration tool for LLMgine-MCP integration.
    
    This tool helps:
    - Analyze existing LLMgine projects
    - Generate MCP server configurations
    - Update engine code
    - Validate migration results
    - Provide rollback capabilities
    """
    
    def __init__(self, project_path: str, backup_dir: Optional[str] = None):
        self.project_path = Path(project_path)
        self.backup_dir = Path(backup_dir) if backup_dir else self.project_path / ".mcp_migration_backup"
        
        # Migration state
        self.analysis_results: Dict[str, Any] = {}
        self.migration_plan: Dict[str, Any] = {}
        self.backup_created = False
        
        logger.info(f"Initialized migrator for project: {self.project_path}")
    
    def analyze_project(self) -> Dict[str, Any]:
        """
        Analyze the existing LLMgine project to understand current tool usage.
        
        Returns:
            Analysis results dictionary
        """
        logger.info("🔍 Analyzing existing LLMgine project...")
        
        analysis = {
            "tool_managers_found": [],
            "engines_found": [],
            "registered_tools": [],
            "potential_mcp_servers": [],
            "migration_complexity": "low"
        }
        
        # Find Python files
        python_files = list(self.project_path.rglob("*.py"))
        logger.info(f"Found {len(python_files)} Python files to analyze")
        
        # Analyze files for ToolManager usage
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Look for ToolManager imports and usage
                if "from llmgine.llm.tools.tool_manager import ToolManager" in content:
                    analysis["tool_managers_found"].append(str(file_path))
                    logger.info(f"Found ToolManager usage in: {file_path}")
                
                # Look for engine classes
                if "class" in content and "Engine" in content:
                    analysis["engines_found"].append(str(file_path))
                
                # Look for tool registration patterns
                if "register_tool(" in content:
                    # Extract registered tool names (basic pattern matching)
                    lines = content.split('\n')
                    for line in lines:
                        if "register_tool(" in line and "def " not in line:
                            analysis["registered_tools"].append({
                                "file": str(file_path),
                                "line": line.strip()
                            })
                
                # Look for potential MCP server candidates
                if any(keyword in content.lower() for keyword in ["calculator", "weather", "search", "notion"]):
                    analysis["potential_mcp_servers"].append(str(file_path))
                
            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {e}")
        
        # Determine migration complexity
        if len(analysis["tool_managers_found"]) > 3:
            analysis["migration_complexity"] = "high"
        elif len(analysis["tool_managers_found"]) > 1:
            analysis["migration_complexity"] = "medium"
        
        self.analysis_results = analysis
        
        # Print analysis summary
        self._print_analysis_summary(analysis)
        
        return analysis
    
    def create_migration_plan(self) -> Dict[str, Any]:
        """
        Create a detailed migration plan based on analysis results.
        
        Returns:
            Migration plan dictionary
        """
        logger.info("📋 Creating migration plan...")
        
        if not self.analysis_results:
            raise RuntimeError("Must run analyze_project() first")
        
        plan = {
            "backup_required": True,
            "files_to_modify": [],
            "mcp_servers_to_create": [],
            "configuration_files": [],
            "validation_steps": []
        }
        
        # Plan file modifications
        for file_path in self.analysis_results["tool_managers_found"]:
            plan["files_to_modify"].append({
                "file": file_path,
                "type": "tool_manager_replacement",
                "changes": [
                    "Replace ToolManager import with MCPToolManager",
                    "Add async initialization",
                    "Add MCP server registration"
                ]
            })
        
        # Plan MCP server creation
        default_servers = [
            {
                "name": "calculator",
                "command": "python",
                "args": ["mcps/demo_calculator.py"],
                "description": "Basic calculator operations"
            },
            {
                "name": "notion",
                "command": "python", 
                "args": ["all_mcp_servers/notion_mcp_server.py"],
                "description": "Notion workspace integration",
                "env": {"NOTION_TOKEN": "${NOTION_TOKEN}"}
            }
        ]
        
        plan["mcp_servers_to_create"] = default_servers
        
        # Plan configuration files
        plan["configuration_files"] = [
            "mcp_servers.yaml",
            ".env.mcp"
        ]
        
        # Plan validation steps
        plan["validation_steps"] = [
            "Verify MCP server connections",
            "Test tool execution",
            "Check event system integration",
            "Run existing tests"
        ]
        
        self.migration_plan = plan
        
        # Print migration plan
        self._print_migration_plan(plan)
        
        return plan
    
    def create_backup(self) -> bool:
        """
        Create backup of the project before migration.
        
        Returns:
            True if backup was successful
        """
        logger.info("💾 Creating project backup...")
        
        try:
            if self.backup_dir.exists():
                shutil.rmtree(self.backup_dir)
            
            # Create backup directory
            self.backup_dir.mkdir(parents=True)
            
            # Copy important files
            files_to_backup = []
            
            # Add all Python files
            files_to_backup.extend(self.project_path.rglob("*.py"))
            
            # Add configuration files
            for pattern in ["*.yaml", "*.yml", "*.json", "*.toml", ".env*"]:
                files_to_backup.extend(self.project_path.rglob(pattern))
            
            backup_count = 0
            for file_path in files_to_backup:
                if file_path.is_file():
                    relative_path = file_path.relative_to(self.project_path)
                    backup_path = self.backup_dir / relative_path
                    
                    # Create parent directories
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file
                    shutil.copy2(file_path, backup_path)
                    backup_count += 1
            
            self.backup_created = True
            logger.info(f"✅ Created backup with {backup_count} files in: {self.backup_dir}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create backup: {e}")
            return False
    
    def execute_migration(self, dry_run: bool = False) -> bool:
        """
        Execute the migration plan.
        
        Args:
            dry_run: If True, only show what would be changed
            
        Returns:
            True if migration was successful
        """
        logger.info(f"🚀 {'Simulating' if dry_run else 'Executing'} migration...")
        
        if not self.migration_plan:
            raise RuntimeError("Must create migration plan first")
        
        if not dry_run and not self.backup_created:
            logger.warning("No backup created - creating backup now")
            if not self.create_backup():
                logger.error("Failed to create backup - aborting migration")
                return False
        
        success = True
        
        try:
            # 1. Modify files
            for file_mod in self.migration_plan["files_to_modify"]:
                success &= self._modify_file(file_mod, dry_run)
            
            # 2. Create MCP server configurations
            success &= self._create_mcp_configuration(dry_run)
            
            # 3. Create environment file
            success &= self._create_environment_file(dry_run)
            
            # 4. Create example migration script
            success &= self._create_example_script(dry_run)
            
            if success:
                logger.info("✅ Migration completed successfully!")
                if not dry_run:
                    self._print_post_migration_instructions()
            else:
                logger.error("❌ Migration completed with errors")
            
        except Exception as e:
            logger.error(f"💥 Migration failed: {e}")
            success = False
        
        return success
    
    def validate_migration(self) -> bool:
        """
        Validate the migration results.
        
        Returns:
            True if validation passed
        """
        logger.info("🔍 Validating migration...")
        
        validation_results = []
        
        # Check if modified files are syntactically correct
        for file_mod in self.migration_plan["files_to_modify"]:
            file_path = Path(file_mod["file"])
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Basic syntax check
                compile(content, str(file_path), 'exec')
                validation_results.append(f"✅ {file_path} - Syntax OK")
                
            except SyntaxError as e:
                validation_results.append(f"❌ {file_path} - Syntax Error: {e}")
            except Exception as e:
                validation_results.append(f"⚠️  {file_path} - Warning: {e}")
        
        # Check configuration files
        config_file = self.project_path / "mcp_servers.yaml"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    yaml.safe_load(f)
                validation_results.append("✅ mcp_servers.yaml - Valid YAML")
            except Exception as e:
                validation_results.append(f"❌ mcp_servers.yaml - Invalid: {e}")
        
        # Print validation results
        logger.info("Validation Results:")
        for result in validation_results:
            logger.info(f"  {result}")
        
        # Return overall success
        return all("❌" not in result for result in validation_results)
    
    def rollback_migration(self) -> bool:
        """
        Rollback the migration using backup files.
        
        Returns:
            True if rollback was successful
        """
        logger.info("↩️  Rolling back migration...")
        
        if not self.backup_created or not self.backup_dir.exists():
            logger.error("No backup found - cannot rollback")
            return False
        
        try:
            # Restore files from backup
            backup_files = list(self.backup_dir.rglob("*"))
            restore_count = 0
            
            for backup_file in backup_files:
                if backup_file.is_file():
                    relative_path = backup_file.relative_to(self.backup_dir)
                    target_path = self.project_path / relative_path
                    
                    # Create parent directories
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Restore file
                    shutil.copy2(backup_file, target_path)
                    restore_count += 1
            
            logger.info(f"✅ Rollback completed - restored {restore_count} files")
            return True
            
        except Exception as e:
            logger.error(f"❌ Rollback failed: {e}")
            return False
    
    def _modify_file(self, file_mod: Dict[str, Any], dry_run: bool) -> bool:
        """Modify a single file according to migration plan."""
        file_path = Path(file_mod["file"])
        
        logger.info(f"{'[DRY RUN] ' if dry_run else ''}Modifying: {file_path}")
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            original_content = content
            
            # Replace ToolManager import
            if "from llmgine.llm.tools.tool_manager import ToolManager" in content:
                content = content.replace(
                    "from llmgine.llm.tools.tool_manager import ToolManager",
                    "from llmgine.llm.tools.mcp_tool_manager import MCPToolManager, MCPServerConfig"
                )
                logger.info(f"  ✅ Updated import statement")
            
            # Replace ToolManager instantiation
            if "ToolManager(" in content:
                # This is a simple replacement - might need more sophisticated parsing
                content = content.replace("ToolManager(", "MCPToolManager(")
                logger.info(f"  ✅ Updated ToolManager instantiation")
            
            # Add initialization comment
            if "MCPToolManager(" in content and "await" not in content:
                # Add comment about needing async initialization
                init_comment = "\n        # TODO: Add async initialization: await self.tool_manager.initialize()\n"
                content = content.replace(
                    "self.tool_manager = MCPToolManager(",
                    f"self.tool_manager = MCPToolManager({init_comment}        # "
                )
            
            # Write modified content
            if not dry_run and content != original_content:
                with open(file_path, 'w') as f:
                    f.write(content)
                logger.info(f"  ✅ File modified successfully")
            elif dry_run:
                logger.info(f"  📋 Would modify file with {len(content) - len(original_content)} character changes")
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Failed to modify {file_path}: {e}")
            return False
    
    def _create_mcp_configuration(self, dry_run: bool) -> bool:
        """Create MCP server configuration file."""
        config_path = self.project_path / "mcp_servers.yaml"
        
        logger.info(f"{'[DRY RUN] ' if dry_run else ''}Creating: {config_path}")
        
        try:
            config = {
                "mcp_servers": self.migration_plan["mcp_servers_to_create"]
            }
            
            if not dry_run:
                with open(config_path, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False)
                logger.info("  ✅ MCP configuration created")
            else:
                logger.info("  📋 Would create MCP configuration file")
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Failed to create MCP configuration: {e}")
            return False
    
    def _create_environment_file(self, dry_run: bool) -> bool:
        """Create environment file template."""
        env_path = self.project_path / ".env.mcp"
        
        logger.info(f"{'[DRY RUN] ' if dry_run else ''}Creating: {env_path}")
        
        try:
            env_content = """# MCP Integration Environment Variables

# Notion Integration
NOTION_TOKEN=your_notion_token_here

# OpenAI API (if using AI features)
OPENAI_API_KEY=your_openai_key_here

# MCP System Configuration
MCP_LOG_LEVEL=INFO
MCP_EXECUTION_TIMEOUT=30
MCP_MAX_RETRIES=3
"""
            
            if not dry_run:
                with open(env_path, 'w') as f:
                    f.write(env_content)
                logger.info("  ✅ Environment file template created")
            else:
                logger.info("  📋 Would create environment file template")
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Failed to create environment file: {e}")
            return False
    
    def _create_example_script(self, dry_run: bool) -> bool:
        """Create example migration script."""
        script_path = self.project_path / "mcp_migration_example.py"
        
        logger.info(f"{'[DRY RUN] ' if dry_run else ''}Creating: {script_path}")
        
        try:
            script_content = '''#!/usr/bin/env python3
"""
Example MCP Integration Script

This script demonstrates how to use the new MCP-based ToolManager
in your LLMgine application.
"""

import asyncio
from llmgine.llm.tools.mcp_tool_manager import MCPToolManager, MCPServerConfig
from llmgine.llm.context.memory import SimpleChatHistory

async def main():
    """Example of using MCPToolManager."""
    
    # Create chat history and tool manager
    chat_history = SimpleChatHistory()
    tool_manager = MCPToolManager(chat_history, "example_session")
    
    try:
        # Initialize MCP system
        await tool_manager.initialize()
        print("✅ MCP ToolManager initialized")
        
        # Register MCP servers
        calculator_config = MCPServerConfig(
            name="calculator",
            command="python",
            args=["mcps/demo_calculator.py"],
            env={},
            auto_start=True
        )
        
        success = await tool_manager.register_mcp_server(calculator_config)
        if success:
            print("✅ Calculator server registered")
        else:
            print("❌ Failed to register calculator server")
        
        # Get available tools
        tools = await tool_manager.discover_mcp_tools()
        print(f"📋 Discovered {len(tools)} MCP tools")
        
        # Get tool schemas (same interface as original ToolManager)
        schemas = tool_manager.tool_schemas
        print(f"🔧 {len(schemas)} tool schemas available")
        
        print("🎉 Migration example completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        # Always cleanup
        await tool_manager.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
'''
            
            if not dry_run:
                with open(script_path, 'w') as f:
                    f.write(script_content)
                # Make script executable
                os.chmod(script_path, 0o755)
                logger.info("  ✅ Example script created")
            else:
                logger.info("  📋 Would create example script")
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Failed to create example script: {e}")
            return False
    
    def _print_analysis_summary(self, analysis: Dict[str, Any]):
        """Print analysis summary."""
        print("\n" + "="*60)
        print("📊 PROJECT ANALYSIS SUMMARY")
        print("="*60)
        print(f"ToolManager files found: {len(analysis['tool_managers_found'])}")
        print(f"Engine files found: {len(analysis['engines_found'])}")
        print(f"Registered tools found: {len(analysis['registered_tools'])}")
        print(f"Migration complexity: {analysis['migration_complexity'].upper()}")
        
        if analysis['tool_managers_found']:
            print("\nFiles using ToolManager:")
            for file_path in analysis['tool_managers_found']:
                print(f"  - {file_path}")
        
        if analysis['registered_tools']:
            print("\nRegistered tools found:")
            for tool in analysis['registered_tools'][:5]:  # Show first 5
                print(f"  - {tool['line']} ({tool['file']})")
            if len(analysis['registered_tools']) > 5:
                print(f"  ... and {len(analysis['registered_tools']) - 5} more")
        
        print("="*60)
    
    def _print_migration_plan(self, plan: Dict[str, Any]):
        """Print migration plan."""
        print("\n" + "="*60)
        print("📋 MIGRATION PLAN")
        print("="*60)
        print(f"Files to modify: {len(plan['files_to_modify'])}")
        print(f"MCP servers to create: {len(plan['mcp_servers_to_create'])}")
        print(f"Configuration files: {len(plan['configuration_files'])}")
        
        print("\nPlanned changes:")
        for file_mod in plan['files_to_modify']:
            print(f"  📝 {file_mod['file']}")
            for change in file_mod['changes']:
                print(f"     - {change}")
        
        print("\nMCP servers to configure:")
        for server in plan['mcp_servers_to_create']:
            print(f"  🔧 {server['name']}: {server['description']}")
        
        print("="*60)
    
    def _print_post_migration_instructions(self):
        """Print post-migration instructions."""
        print("\n" + "="*60)
        print("🎉 MIGRATION COMPLETED!")
        print("="*60)
        print("\nNext steps:")
        print("1. Review modified files and add async initialization where needed")
        print("2. Configure environment variables in .env.mcp")
        print("3. Test MCP server connections")
        print("4. Run the example script: python mcp_migration_example.py")
        print("5. Update your application's async initialization")
        print("6. Run existing tests to ensure compatibility")
        
        print("\nKey changes made:")
        print("- Replaced ToolManager imports with MCPToolManager")
        print("- Created mcp_servers.yaml configuration")
        print("- Created .env.mcp environment template")
        print("- Generated example integration script")
        
        print("\nImportant notes:")
        print("- MCPToolManager requires async initialization")
        print("- Add 'await tool_manager.initialize()' in your code")
        print("- MCP servers need to be started before use")
        print("- Backup created in:", self.backup_dir)
        
        print("="*60)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate LLMgine project to use MCP-based ToolManager"
    )
    
    parser.add_argument(
        "project_path",
        help="Path to LLMgine project directory"
    )
    
    parser.add_argument(
        "--backup-dir",
        help="Custom backup directory (default: PROJECT_PATH/.mcp_migration_backup)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making modifications"
    )
    
    parser.add_argument(
        "--skip-backup",
        action="store_true",
        help="Skip creating backup (not recommended)"
    )
    
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Rollback previous migration using backup"
    )
    
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate existing migration"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create migrator
    migrator = LLMgineMCPMigrator(args.project_path, args.backup_dir)
    
    try:
        if args.rollback:
            # Rollback migration
            success = migrator.rollback_migration()
            sys.exit(0 if success else 1)
        
        if args.validate_only:
            # Validate existing migration
            success = migrator.validate_migration()
            sys.exit(0 if success else 1)
        
        # Standard migration workflow
        print("🚀 Starting LLMgine-MCP Migration")
        print("="*50)
        
        # 1. Analyze project
        analysis = migrator.analyze_project()
        
        # 2. Create migration plan
        plan = migrator.create_migration_plan()
        
        # 3. Create backup (unless skipped)
        if not args.skip_backup and not args.dry_run:
            backup_success = migrator.create_backup()
            if not backup_success:
                logger.error("Failed to create backup - aborting")
                sys.exit(1)
        
        # 4. Execute migration
        migration_success = migrator.execute_migration(args.dry_run)
        
        # 5. Validate migration (if not dry run)
        if not args.dry_run and migration_success:
            validation_success = migrator.validate_migration()
            if not validation_success:
                logger.warning("Migration completed but validation failed")
        
        # Exit with appropriate code
        sys.exit(0 if migration_success else 1)
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

