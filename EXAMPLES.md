# Keyboard Maestro MCP Server: Practical Examples

## Overview

This guide provides comprehensive, real-world examples demonstrating the capabilities of the Keyboard Maestro MCP Server. Each example includes complete code, error handling, and explanations of integration patterns with AI assistants.

**🎯 Example Categories:**
- **Basic Automation**: Simple macro execution and variable management
- **Complex Workflows**: Multi-step processes with error handling  
- **AI Assistant Integration**: Advanced patterns for LLM-driven automation
- **System Administration**: Bulk operations and monitoring
- **Error Handling**: Comprehensive error recovery strategies
- **Performance Optimization**: Efficient automation patterns

## Table of Contents

1. [Basic Automation Examples](#1-basic-automation-examples)
2. [Complex Workflow Examples](#2-complex-workflow-examples)  
3. [AI Assistant Integration Patterns](#3-ai-assistant-integration-patterns)
4. [System Administration Examples](#4-system-administration-examples)
5. [Error Handling Demonstrations](#5-error-handling-demonstrations)
6. [Performance Optimization Examples](#6-performance-optimization-examples)
7. [Advanced Integration Scenarios](#7-advanced-integration-scenarios)

---

## 1. Basic Automation Examples

### Example 1.1: Simple Macro Execution

**Scenario**: Execute a macro to open a specific application and set up workspace.

```python
from fastmcp import Client
import asyncio

async def execute_daily_setup():
    """Execute daily workspace setup macro."""
    
    async with Client("stdio:keyboard-maestro-mcp") as client:
        try:
            # Execute the daily setup macro
            result = await client.call_tool("km_execute_macro", {
                "identifier": "Daily Workspace Setup",
                "timeout": 60
            })
            
            print(f"✅ Setup complete: {result[0].text}")
            
            # Extract execution details
            data = eval(result[0].text)  # In real code, use json.loads
            print(f"Execution time: {data['execution_time']:.2f}s")
            print(f"Macro ID: {data['macro_id']}")
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")

# Run the example
asyncio.run(execute_daily_setup())
```

**Expected Output:**
```
✅ Setup complete: {"success": true, "data": {"execution_id": "...", "macro_name": "Daily Workspace Setup", "execution_time": 0.45}}
Execution time: 0.45s
Macro ID: 550e8400-e29b-41d4-a716-446655440000
```

### Example 1.2: Variable Management

**Scenario**: Store and retrieve project information across automation sessions.

```python
async def manage_project_variables():
    """Demonstrate variable management for project automation."""
    
    async with Client("stdio:keyboard-maestro-mcp") as client:
        
        # Set project configuration variables
        project_config = {
            "ProjectName": "AI Assistant Integration",
            "ProjectDeadline": "2025-07-01",
            "ProjectStatus": "In Progress",
            "TeamLead": "John Doe",
            "Priority": "High"
        }
        
        print("📝 Setting project variables...")
        for name, value in project_config.items():
            await client.call_tool("km_variable_manager", {
                "operation": "set",
                "name": name,
                "value": str(value),
                "scope": "global"
            })
            print(f"  ✅ Set {name} = {value}")
        
        # Retrieve and display all project variables
        print("\n📖 Reading project variables...")
        for name in project_config.keys():
            result = await client.call_tool("km_variable_manager", {
                "operation": "get",
                "name": name,
                "scope": "global"
            })
            print(f"  📄 {name}: {result[0].text}")

asyncio.run(manage_project_variables())
```

### Example 1.3: Clipboard Operations

**Scenario**: Process text through clipboard with formatting automation.

```python
async def clipboard_text_processing():
    """Process clipboard content with automated formatting."""
    
    async with Client("stdio:keyboard-maestro-mcp") as client:
        
        # Get current clipboard content
        result = await client.call_tool("km_clipboard_manager", {
            "operation": "get",
            "format": "text"
        })
        
        original_text = result[0].text
        print(f"📋 Original text: {original_text[:50]}...")
        
        # Process text (example: convert to title case)
        processed_text = original_text.title()
        
        # Set processed text back to clipboard
        await client.call_tool("km_clipboard_manager", {
            "operation": "set",
            "content": processed_text,
            "format": "text"
        })
        
        print(f"✅ Processed text set to clipboard")
        
        # Optionally save to named clipboard for backup
        await client.call_tool("km_clipboard_manager", {
            "operation": "manage_named",
            "clipboard_name": "ProcessedText_Backup",
            "content": processed_text
        })
        
        print(f"💾 Backup saved to named clipboard")

asyncio.run(clipboard_text_processing())
```

---

## 2. Complex Workflow Examples

### Example 2.1: Document Processing Pipeline

**Scenario**: Automated document review workflow with OCR, processing, and notification.

```python
async def document_processing_pipeline(document_path: str):
    """Complete document processing workflow with multiple automation steps."""
    
    async with Client("stdio:keyboard-maestro-mcp") as client:
        
        workflow_id = f"doc_process_{int(time.time())}"
        
        try:
            # Step 1: Set workflow tracking variables
            await client.call_tool("km_variable_manager", {
                "operation": "set",
                "name": f"WorkflowID_{workflow_id}",
                "value": "STARTED",
                "scope": "global"
            })
            
            print(f"🚀 Starting document processing workflow: {workflow_id}")
            
            # Step 2: OCR the document for text extraction
            print("📝 Extracting text with OCR...")
            ocr_result = await client.call_tool("km_visual_automation", {
                "operation": "ocr",
                "area": "screen",  # Or specific coordinates
                "language": "en"
            })
            
            extracted_text = ocr_result[0].text
            print(f"📄 Extracted {len(extracted_text)} characters")
            
            # Step 3: Save extracted text to variable
            await client.call_tool("km_variable_manager", {
                "operation": "set",
                "name": f"ExtractedText_{workflow_id}",
                "value": extracted_text,
                "scope": "global"
            })
            
            # Step 4: Process document with macro
            print("⚙️ Processing document with macro...")
            process_result = await client.call_tool("km_execute_macro", {
                "identifier": "Document Processor",
                "trigger_value": workflow_id,
                "timeout": 120
            })
            
            # Step 5: Send completion notification
            print("📧 Sending completion notification...")
            await client.call_tool("km_notifications", {
                "type": "notification",
                "title": "Document Processing Complete",
                "message": f"Workflow {workflow_id} finished successfully",
                "sound": "Purr"
            })
            
            # Step 6: Update workflow status
            await client.call_tool("km_variable_manager", {
                "operation": "set",
                "name": f"WorkflowID_{workflow_id}",
                "value": "COMPLETED",
                "scope": "global"
            })
            
            print(f"✅ Workflow {workflow_id} completed successfully")
            
        except Exception as e:
            # Error handling: Update status and notify
            await client.call_tool("km_variable_manager", {
                "operation": "set",
                "name": f"WorkflowID_{workflow_id}",
                "value": f"ERROR: {str(e)}",
                "scope": "global"
            })
            
            await client.call_tool("km_notifications", {
                "type": "alert",
                "title": "Document Processing Failed",
                "message": f"Workflow {workflow_id} encountered an error: {str(e)}"
            })
            
            print(f"❌ Workflow {workflow_id} failed: {e}")
            raise

# Example usage
asyncio.run(document_processing_pipeline("/path/to/document.pdf"))
```

### Example 2.2: Multi-Application Workflow

**Scenario**: Complex workflow involving multiple applications and data synchronization.

```python
async def multi_app_data_sync():
    """Synchronize data across multiple applications with error recovery."""
    
    async with Client("stdio:keyboard-maestro-mcp") as client:
        
        applications = [
            {"name": "Notion", "bundle_id": "notion.id"},
            {"name": "Airtable", "bundle_id": "com.airtable.airtable"},
            {"name": "Excel", "bundle_id": "com.microsoft.Excel"}
        ]
        
        print("🔄 Starting multi-application data synchronization...")
        
        # Step 1: Ensure all required applications are available
        for app in applications:
            try:
                await client.call_tool("km_app_control", {
                    "operation": "activate",
                    "app_identifier": app["bundle_id"]
                })
                print(f"✅ {app['name']} is ready")
            except Exception as e:
                print(f"⚠️ {app['name']} not available: {e}")
                
                # Attempt to launch the application
                try:
                    await client.call_tool("km_app_control", {
                        "operation": "launch",
                        "app_identifier": app["bundle_id"]
                    })
                    print(f"🚀 Launched {app['name']}")
                except Exception as launch_error:
                    print(f"❌ Failed to launch {app['name']}: {launch_error}")
                    continue
        
        # Step 2: Execute data extraction macro for each application
        extracted_data = {}
        
        for app in applications:
            try:
                print(f"📊 Extracting data from {app['name']}...")
                
                # Execute app-specific data extraction macro
                result = await client.call_tool("km_execute_macro", {
                    "identifier": f"Extract Data from {app['name']}",
                    "timeout": 60
                })
                
                # Store extracted data
                data_key = f"Data_{app['name'].replace(' ', '_')}"
                extracted_data[data_key] = result[0].text
                
                await client.call_tool("km_variable_manager", {
                    "operation": "set",
                    "name": data_key,
                    "value": result[0].text,
                    "scope": "global"
                })
                
                print(f"✅ Data extracted from {app['name']}")
                
            except Exception as e:
                print(f"⚠️ Data extraction failed for {app['name']}: {e}")
                # Continue with other applications
                continue
        
        # Step 3: Process and synchronize data
        if extracted_data:
            print("🔄 Processing extracted data...")
            
            # Execute data processing macro
            await client.call_tool("km_execute_macro", {
                "identifier": "Data Synchronization Processor",
                "trigger_value": ",".join(extracted_data.keys()),
                "timeout": 180
            })
            
            print("✅ Data synchronization completed")
        else:
            print("❌ No data was successfully extracted")

asyncio.run(multi_app_data_sync())
```

---

## 3. AI Assistant Integration Patterns

### Example 3.1: AI-Driven Macro Creation

**Scenario**: Use AI to analyze requirements and create appropriate macros dynamically.

```python
async def ai_driven_macro_creation(user_requirements: str):
    """Create macros based on AI analysis of user requirements."""
    
    async with Client("stdio:keyboard-maestro-mcp") as client:
        
        print(f"🤖 Analyzing requirements: {user_requirements}")
        
        # This would typically involve an LLM analyzing the requirements
        # For this example, we'll simulate the AI decision-making process
        
        # Simulated AI analysis results
        macro_specs = {
            "name": "AI Generated Workflow",
            "description": f"Automated workflow based on: {user_requirements}",
            "triggers": [
                {
                    "type": "hotkey",
                    "key": "F1",
                    "modifiers": ["Command", "Option"]
                }
            ],
            "actions": [
                {
                    "type": "notification",
                    "title": "AI Workflow",
                    "message": "Executing AI-generated automation"
                }
            ]
        }
        
        try:
            # Create the macro group for AI-generated macros
            await client.call_tool("km_manage_macro_group", {
                "operation": "create",
                "properties": {
                    "name": "AI Generated Macros",
                    "enabled": True,
                    "activation_method": "always"
                }
            })
            
            # Create the macro
            print("🛠️ Creating AI-generated macro...")
            result = await client.call_tool("km_create_macro", {
                "name": macro_specs["name"],
                "group_id": "AI Generated Macros",  # Would use actual UUID
                "enabled": True,
                "notes": macro_specs["description"],
                "triggers": macro_specs["triggers"],
                "actions": macro_specs["actions"]
            })
            
            print(f"✅ Created macro: {macro_specs['name']}")
            
            # Test the created macro
            print("🧪 Testing the new macro...")
            test_result = await client.call_tool("km_execute_macro", {
                "identifier": macro_specs["name"],
                "timeout": 30
            })
            
            print(f"✅ Macro tested successfully: {test_result[0].text}")
            
            return macro_specs["name"]
            
        except Exception as e:
            print(f"❌ Macro creation failed: {e}")
            raise

# Example usage
asyncio.run(ai_driven_macro_creation("Create a workflow that opens my daily productivity apps and sets up my workspace"))
```

### Example 3.2: Intelligent Error Recovery

**Scenario**: AI assistant that can diagnose and recover from automation failures.

```python
async def intelligent_error_recovery(failed_macro_id: str, error_context: dict):
    """Implement intelligent error recovery with AI decision-making."""
    
    async with Client("stdio:keyboard-maestro-mcp") as client:
        
        print(f"🔍 Analyzing failure for macro: {failed_macro_id}")
        print(f"📊 Error context: {error_context}")
        
        # Step 1: Gather diagnostic information
        diagnostic_info = {}
        
        # Check system status
        try:
            status_result = await client.call_tool("km_engine_status", {
                "operation": "status"
            })
            diagnostic_info["engine_status"] = status_result[0].text
        except Exception as e:
            diagnostic_info["engine_status"] = f"Error: {e}"
        
        # Check application states
        if "target_app" in error_context:
            try:
                app_result = await client.call_tool("km_app_control", {
                    "operation": "activate",
                    "app_identifier": error_context["target_app"]
                })
                diagnostic_info["app_status"] = "Available"
            except Exception as e:
                diagnostic_info["app_status"] = f"Unavailable: {e}"
        
        # Check variable states
        if "required_variables" in error_context:
            diagnostic_info["variables"] = {}
            for var_name in error_context["required_variables"]:
                try:
                    var_result = await client.call_tool("km_variable_manager", {
                        "operation": "get",
                        "name": var_name,
                        "scope": "global"
                    })
                    diagnostic_info["variables"][var_name] = var_result[0].text
                except Exception as e:
                    diagnostic_info["variables"][var_name] = f"Missing: {e}"
        
        # Step 2: AI-driven recovery strategy selection
        # In a real implementation, this would use an LLM to analyze the diagnostic info
        
        recovery_strategies = []
        
        # Strategy 1: Restart Keyboard Maestro Engine
        if "timeout" in str(error_context).lower():
            recovery_strategies.append("restart_engine")
        
        # Strategy 2: Reset application state
        if diagnostic_info.get("app_status", "").startswith("Unavailable"):
            recovery_strategies.append("reset_application")
        
        # Strategy 3: Restore missing variables
        if any("Missing" in str(v) for v in diagnostic_info.get("variables", {}).values()):
            recovery_strategies.append("restore_variables")
        
        print(f"🎯 Selected recovery strategies: {recovery_strategies}")
        
        # Step 3: Execute recovery strategies
        for strategy in recovery_strategies:
            try:
                if strategy == "restart_engine":
                    print("🔄 Restarting Keyboard Maestro Engine...")
                    await client.call_tool("km_engine_status", {
                        "operation": "reload"
                    })
                    
                elif strategy == "reset_application":
                    print("🔄 Resetting application state...")
                    if "target_app" in error_context:
                        # Quit and restart the application
                        await client.call_tool("km_app_control", {
                            "operation": "quit",
                            "app_identifier": error_context["target_app"]
                        })
                        await asyncio.sleep(2)  # Wait for clean shutdown
                        await client.call_tool("km_app_control", {
                            "operation": "launch",
                            "app_identifier": error_context["target_app"]
                        })
                
                elif strategy == "restore_variables":
                    print("🔄 Restoring missing variables...")
                    # Execute variable restoration macro
                    await client.call_tool("km_execute_macro", {
                        "identifier": "Restore Default Variables",
                        "timeout": 30
                    })
                
                print(f"✅ Recovery strategy '{strategy}' completed")
                
            except Exception as e:
                print(f"❌ Recovery strategy '{strategy}' failed: {e}")
                continue
        
        # Step 4: Retry the original macro
        print("🔄 Retrying original macro...")
        try:
            retry_result = await client.call_tool("km_execute_macro", {
                "identifier": failed_macro_id,
                "timeout": 60
            })
            
            print(f"✅ Macro retry successful: {retry_result[0].text}")
            return True
            
        except Exception as e:
            print(f"❌ Macro retry failed: {e}")
            
            # Log the failure for further analysis
            await client.call_tool("km_variable_manager", {
                "operation": "set",
                "name": f"FailureLog_{failed_macro_id}_{int(time.time())}",
                "value": f"Recovery failed: {str(e)}",
                "scope": "global"
            })
            
            return False

# Example usage
error_context = {
    "target_app": "com.microsoft.Word",
    "required_variables": ["DocumentPath", "TemplateLocation"],
    "error_type": "timeout",
    "last_action": "file_operation"
}

asyncio.run(intelligent_error_recovery("Document Generator", error_context))
```

### Example 3.3: Context-Aware Automation

**Scenario**: AI assistant that adapts automation based on current context and user behavior.

```python
async def context_aware_automation():
    """Implement context-aware automation that adapts to current conditions."""
    
    async with Client("stdio:keyboard-maestro-mcp") as client:
        
        print("🔍 Analyzing current context...")
        
        # Gather contextual information
        context = {}
        
        # Get current time and date context
        import datetime
        now = datetime.datetime.now()
        context["time_of_day"] = now.strftime("%H:%M")
        context["day_of_week"] = now.strftime("%A")
        context["is_weekend"] = now.weekday() >= 5
        
        # Get current active application
        try:
            # This would typically get the front application
            context["active_app"] = "com.microsoft.Word"  # Example
        except Exception as e:
            context["active_app"] = "unknown"
        
        # Get current project context from variables
        try:
            project_result = await client.call_tool("km_variable_manager", {
                "operation": "get",
                "name": "CurrentProject",
                "scope": "global"
            })
            context["current_project"] = project_result[0].text
        except Exception:
            context["current_project"] = "none"
        
        # Check system load
        try:
            system_result = await client.call_tool("km_engine_status", {
                "operation": "status"
            })
            context["system_load"] = "normal"  # Would parse actual status
        except Exception:
            context["system_load"] = "unknown"
        
        print(f"📊 Context analysis complete: {context}")
        
        # AI-driven context adaptation logic
        automation_plan = []
        
        # Time-based adaptations
        if context["time_of_day"] < "09:00":
            automation_plan.append("morning_setup")
        elif context["time_of_day"] > "17:00":
            automation_plan.append("evening_cleanup")
        
        # Weekend vs weekday adaptations
        if context["is_weekend"]:
            automation_plan.append("weekend_mode")
        else:
            automation_plan.append("work_mode")
        
        # Application-specific adaptations
        if "word" in context["active_app"].lower():
            automation_plan.append("document_assistance")
        elif "excel" in context["active_app"].lower():
            automation_plan.append("spreadsheet_assistance")
        
        # Project-specific adaptations
        if context["current_project"] != "none":
            automation_plan.append("project_specific_tools")
        
        print(f"🎯 Automation plan: {automation_plan}")
        
        # Execute context-appropriate automations
        for automation in automation_plan:
            try:
                print(f"⚙️ Executing: {automation}")
                
                # Map automation to actual macro execution
                macro_mapping = {
                    "morning_setup": "Daily Morning Setup",
                    "evening_cleanup": "Daily Cleanup Routine",
                    "weekend_mode": "Weekend Productivity Mode",
                    "work_mode": "Work Environment Setup",
                    "document_assistance": "Document Helper Tools",
                    "spreadsheet_assistance": "Excel Productivity Tools",
                    "project_specific_tools": "Project Context Tools"
                }
                
                if automation in macro_mapping:
                    result = await client.call_tool("km_execute_macro", {
                        "identifier": macro_mapping[automation],
                        "timeout": 45
                    })
                    print(f"✅ {automation} completed")
                
            except Exception as e:
                print(f"⚠️ {automation} failed: {e}")
                continue
        
        # Update context tracking for future adaptations
        await client.call_tool("km_variable_manager", {
            "operation": "set",
            "name": "LastContextAdaptation",
            "value": str(context),
            "scope": "global"
        })
        
        print("✅ Context-aware automation completed")

asyncio.run(context_aware_automation())
```

---

## 4. System Administration Examples

### Example 4.1: Bulk Macro Management

**Scenario**: System administrator managing large sets of macros across multiple users or environments.

```python
async def bulk_macro_management():
    """Demonstrate bulk operations for system administration."""
    
    async with Client("stdio:keyboard-maestro-mcp") as client:
        
        print("🔧 Starting bulk macro management operations...")
        
        # Step 1: Export all macros for backup
        print("💾 Backing up all macros...")
        
        try:
            # Get list of all macros
            macros_result = await client.call_tool("km_list_macros", {
                "include_disabled": True,
                "include_groups": True
            })
            
            macro_list = eval(macros_result[0].text)  # In production, use json.loads
            print(f"📊 Found {len(macro_list)} macros to backup")
            
            # Export all macros
            for macro in macro_list[:5]:  # Limit for example
                try:
                    export_result = await client.call_tool("km_import_export_macro", {
                        "operation": "export",
                        "format": "kmmacros",
                        "path": f"/tmp/backup_{macro['id']}.kmmacros",
                        "macro_ids": [macro['id']]
                    })
                    print(f"✅ Backed up: {macro['name']}")
                    
                except Exception as e:
                    print(f"⚠️ Backup failed for {macro['name']}: {e}")
            
        except Exception as e:
            print(f"❌ Macro listing failed: {e}")
            return
        
        # Step 2: Bulk update macro properties
        print("\n🔄 Updating macro properties...")
        
        update_rules = [
            {"pattern": "Test", "enabled": False, "color": "Red"},
            {"pattern": "Production", "enabled": True, "color": "Green"},
            {"pattern": "Debug", "enabled": False, "color": "Yellow"}
        ]
        
        for rule in update_rules:
            matching_macros = [m for m in macro_list if rule["pattern"] in m.get("name", "")]
            
            for macro in matching_macros:
                try:
                    await client.call_tool("km_manage_macro_properties", {
                        "operation": "update",
                        "macro_id": macro["id"],
                        "properties": {
                            "enabled": rule["enabled"],
                            "color": rule["color"]
                        }
                    })
                    print(f"✅ Updated {macro['name']}: enabled={rule['enabled']}, color={rule['color']}")
                    
                except Exception as e:
                    print(f"⚠️ Update failed for {macro['name']}: {e}")
        
        # Step 3: Create standardized macro groups
        print("\n📁 Creating standardized macro groups...")
        
        standard_groups = [
            {"name": "System Administration", "activation": "always"},
            {"name": "Development Tools", "activation": "always"},
            {"name": "Testing Utilities", "activation": "one_action"}
        ]
        
        for group in standard_groups:
            try:
                await client.call_tool("km_manage_macro_group", {
                    "operation": "create",
                    "properties": {
                        "name": group["name"],
                        "enabled": True,
                        "activation_method": group["activation"]
                    }
                })
                print(f"✅ Created group: {group['name']}")
                
            except Exception as e:
                print(f"⚠️ Group creation failed for {group['name']}: {e}")
        
        # Step 4: Generate management report
        print("\n📊 Generating management report...")
        
        report_data = {
            "total_macros": len(macro_list),
            "enabled_macros": len([m for m in macro_list if m.get("enabled", True)]),
            "disabled_macros": len([m for m in macro_list if not m.get("enabled", True)]),
            "groups_created": len(standard_groups),
            "backup_timestamp": datetime.datetime.now().isoformat()
        }
        
        # Save report to variable
        await client.call_tool("km_variable_manager", {
            "operation": "set",
            "name": "SystemManagementReport",
            "value": str(report_data),
            "scope": "global"
        })
        
        print(f"📈 Management report: {report_data}")
        print("✅ Bulk macro management completed")

asyncio.run(bulk_macro_management())
```

### Example 4.2: System Health Monitoring

**Scenario**: Automated monitoring and maintenance of Keyboard Maestro system health.

```python
async def system_health_monitoring():
    """Monitor and maintain Keyboard Maestro system health."""
    
    async with Client("stdio:keyboard-maestro-mcp") as client:
        
        print("🏥 Starting system health monitoring...")
        
        health_report = {
            "timestamp": datetime.datetime.now().isoformat(),
            "engine_status": "unknown",
            "macro_count": 0,
            "error_count": 0,
            "performance_metrics": {},
            "recommendations": []
        }
        
        # Check 1: Engine Status
        print("🔍 Checking Keyboard Maestro Engine status...")
        try:
            engine_result = await client.call_tool("km_engine_status", {
                "operation": "status"
            })
            health_report["engine_status"] = "running"
            print("✅ Engine is running")
        except Exception as e:
            health_report["engine_status"] = f"error: {e}"
            health_report["recommendations"].append("Restart Keyboard Maestro Engine")
            print(f"❌ Engine status check failed: {e}")
        
        # Check 2: Macro Inventory
        print("📊 Checking macro inventory...")
        try:
            macros_result = await client.call_tool("km_list_macros", {
                "include_disabled": True
            })
            macro_data = eval(macros_result[0].text)
            health_report["macro_count"] = len(macro_data)
            
            # Analyze macro health
            disabled_count = len([m for m in macro_data if not m.get("enabled", True)])
            if disabled_count > health_report["macro_count"] * 0.3:
                health_report["recommendations"].append(
                    f"High number of disabled macros ({disabled_count}). Review and clean up."
                )
            
            print(f"📈 Found {health_report['macro_count']} macros ({disabled_count} disabled)")
            
        except Exception as e:
            health_report["recommendations"].append("Unable to retrieve macro inventory")
            print(f"❌ Macro inventory check failed: {e}")
        
        # Check 3: Variable Management
        print("🔧 Checking variable usage...")
        try:
            # Check for common variables
            test_variables = ["LastBackup", "SystemStatus", "ErrorLog"]
            variable_status = {}
            
            for var_name in test_variables:
                try:
                    var_result = await client.call_tool("km_variable_manager", {
                        "operation": "get",
                        "name": var_name,
                        "scope": "global"
                    })
                    variable_status[var_name] = "exists"
                except Exception:
                    variable_status[var_name] = "missing"
            
            missing_vars = [k for k, v in variable_status.items() if v == "missing"]
            if missing_vars:
                health_report["recommendations"].append(
                    f"Initialize missing system variables: {', '.join(missing_vars)}"
                )
            
            print(f"📝 Variable status: {variable_status}")
            
        except Exception as e:
            health_report["recommendations"].append("Variable system check failed")
            print(f"❌ Variable check failed: {e}")
        
        # Check 4: Performance Testing
        print("⚡ Running performance tests...")
        try:
            import time
            
            # Test simple macro execution speed
            start_time = time.time()
            await client.call_tool("km_execute_macro", {
                "identifier": "System Health Test",  # Simple test macro
                "timeout": 10
            })
            execution_time = time.time() - start_time
            
            health_report["performance_metrics"]["simple_execution"] = execution_time
            
            if execution_time > 2.0:
                health_report["recommendations"].append("Slow macro execution detected. Check system resources.")
            
            print(f"⏱️ Simple execution time: {execution_time:.2f}s")
            
        except Exception as e:
            health_report["recommendations"].append("Performance testing failed")
            print(f"❌ Performance test failed: {e}")
        
        # Check 5: Error Log Analysis
        print("📋 Analyzing error logs...")
        try:
            log_result = await client.call_tool("km_engine_status", {
                "operation": "logs",
                "log_lines": 100
            })
            
            log_content = log_result[0].text
            error_keywords = ["error", "failed", "timeout", "exception"]
            
            error_lines = []
            for line in log_content.split("\n"):
                if any(keyword in line.lower() for keyword in error_keywords):
                    error_lines.append(line)
            
            health_report["error_count"] = len(error_lines)
            
            if health_report["error_count"] > 10:
                health_report["recommendations"].append(
                    f"High error count ({health_report['error_count']}). Review recent failures."
                )
            
            print(f"🚨 Found {health_report['error_count']} error entries in recent logs")
            
        except Exception as e:
            health_report["recommendations"].append("Error log analysis failed")
            print(f"❌ Log analysis failed: {e}")
        
        # Generate Health Score
        score = 100
        score -= len(health_report["recommendations"]) * 10
        score -= health_report["error_count"] * 2
        if health_report["engine_status"] != "running":
            score -= 30
        
        health_report["health_score"] = max(0, score)
        
        # Save health report
        await client.call_tool("km_variable_manager", {
            "operation": "set",
            "name": "LastHealthReport",
            "value": str(health_report),
            "scope": "global"
        })
        
        # Send notification if health is poor
        if health_report["health_score"] < 70:
            await client.call_tool("km_notifications", {
                "type": "alert",
                "title": "System Health Warning",
                "message": f"Health score: {health_report['health_score']}/100. Check recommendations."
            })
        
        print(f"\n🏆 System Health Score: {health_report['health_score']}/100")
        print(f"📋 Recommendations: {len(health_report['recommendations'])}")
        for rec in health_report["recommendations"]:
            print(f"  • {rec}")
        
        print("✅ System health monitoring completed")

asyncio.run(system_health_monitoring())
```

---

## 5. Error Handling Demonstrations

### Example 5.1: Comprehensive Error Recovery

**Scenario**: Robust error handling patterns for production automation systems.

```python
import asyncio
import logging
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ErrorContext:
    error_type: str
    severity: ErrorSeverity
    retry_count: int
    max_retries: int
    recovery_strategies: List[str]
    metadata: Dict

class RobustAutomationManager:
    """Comprehensive error handling and recovery for automation workflows."""
    
    def __init__(self, client):
        self.client = client
        self.error_history = []
        self.recovery_strategies = {
            "restart_engine": self._restart_engine,
            "reset_variables": self._reset_variables,
            "reload_macros": self._reload_macros,
            "cleanup_temp_files": self._cleanup_temp_files,
            "restart_applications": self._restart_applications
        }
    
    async def execute_with_recovery(self, 
                                   operation: Callable,
                                   error_context: ErrorContext,
                                   *args, **kwargs) -> Optional[any]:
        """Execute operation with comprehensive error handling and recovery."""
        
        for attempt in range(error_context.max_retries + 1):
            try:
                print(f"🔄 Attempt {attempt + 1}/{error_context.max_retries + 1}")
                
                # Execute the operation
                result = await operation(*args, **kwargs)
                
                # Log successful execution
                await self._log_success(operation.__name__, attempt, error_context)
                return result
                
            except Exception as e:
                # Log the error
                await self._log_error(e, attempt, error_context)
                
                # If this was the last attempt, raise the error
                if attempt >= error_context.max_retries:
                    await self._handle_final_failure(e, error_context)
                    raise
                
                # Attempt recovery strategies
                recovered = await self._attempt_recovery(e, error_context)
                
                if not recovered and error_context.severity == ErrorSeverity.CRITICAL:
                    # For critical errors, don't retry if recovery failed
                    await self._handle_final_failure(e, error_context)
                    raise
                
                # Wait before retry (exponential backoff)
                wait_time = 2 ** attempt
                print(f"⏳ Waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)
    
    async def _attempt_recovery(self, error: Exception, context: ErrorContext) -> bool:
        """Attempt recovery strategies based on error type and context."""
        
        print(f"🔧 Attempting recovery for: {type(error).__name__}")
        
        recovery_success = False
        
        for strategy in context.recovery_strategies:
            if strategy in self.recovery_strategies:
                try:
                    print(f"🛠️ Executing recovery strategy: {strategy}")
                    await self.recovery_strategies[strategy](error, context)
                    recovery_success = True
                    print(f"✅ Recovery strategy '{strategy}' succeeded")
                    break
                    
                except Exception as recovery_error:
                    print(f"❌ Recovery strategy '{strategy}' failed: {recovery_error}")
                    continue
        
        return recovery_success
    
    async def _restart_engine(self, error: Exception, context: ErrorContext):
        """Restart Keyboard Maestro Engine."""
        await self.client.call_tool("km_engine_status", {
            "operation": "reload"
        })
        await asyncio.sleep(3)  # Wait for engine to restart
    
    async def _reset_variables(self, error: Exception, context: ErrorContext):
        """Reset critical system variables."""
        critical_variables = context.metadata.get("critical_variables", [])
        
        for var_name in critical_variables:
            try:
                await self.client.call_tool("km_variable_manager", {
                    "operation": "delete",
                    "name": var_name,
                    "scope": "global"
                })
            except Exception:
                pass  # Variable might not exist
        
        # Execute variable initialization macro
        await self.client.call_tool("km_execute_macro", {
            "identifier": "Initialize System Variables",
            "timeout": 30
        })
    
    async def _reload_macros(self, error: Exception, context: ErrorContext):
        """Reload all macros."""
        await self.client.call_tool("km_engine_status", {
            "operation": "reload"
        })
    
    async def _cleanup_temp_files(self, error: Exception, context: ErrorContext):
        """Clean up temporary files that might be causing issues."""
        temp_paths = context.metadata.get("temp_paths", [])
        
        for path in temp_paths:
            try:
                await self.client.call_tool("km_file_operations", {
                    "operation": "delete",
                    "source_path": path
                })
            except Exception:
                pass  # File might not exist
    
    async def _restart_applications(self, error: Exception, context: ErrorContext):
        """Restart applications involved in the workflow."""
        target_apps = context.metadata.get("target_applications", [])
        
        for app in target_apps:
            try:
                # Quit the application
                await self.client.call_tool("km_app_control", {
                    "operation": "quit",
                    "app_identifier": app
                })
                await asyncio.sleep(2)
                
                # Restart the application
                await self.client.call_tool("km_app_control", {
                    "operation": "launch",
                    "app_identifier": app
                })
                await asyncio.sleep(3)
                
            except Exception as app_error:
                print(f"⚠️ Failed to restart {app}: {app_error}")
    
    async def _log_error(self, error: Exception, attempt: int, context: ErrorContext):
        """Log error details for analysis."""
        error_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "attempt": attempt,
            "severity": context.severity.value,
            "context": context.metadata
        }
        
        self.error_history.append(error_entry)
        
        # Save to Keyboard Maestro variable for persistence
        await self.client.call_tool("km_variable_manager", {
            "operation": "set",
            "name": f"ErrorLog_{int(time.time())}",
            "value": str(error_entry),
            "scope": "global"
        })
        
        print(f"📝 Logged error: {error_entry}")
    
    async def _log_success(self, operation: str, attempts: int, context: ErrorContext):
        """Log successful execution after recovery."""
        if attempts > 0:
            success_entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "operation": operation,
                "attempts_required": attempts + 1,
                "severity": context.severity.value,
                "recovered": True
            }
            
            await self.client.call_tool("km_variable_manager", {
                "operation": "set",
                "name": f"RecoverySuccess_{int(time.time())}",
                "value": str(success_entry),
                "scope": "global"
            })
            
            print(f"🎉 Recovery successful after {attempts + 1} attempts")
    
    async def _handle_final_failure(self, error: Exception, context: ErrorContext):
        """Handle final failure when all recovery attempts exhausted."""
        
        # Send critical notification
        await self.client.call_tool("km_notifications", {
            "type": "alert",
            "title": "Critical Automation Failure",
            "message": f"Operation failed after {context.max_retries} attempts: {str(error)[:100]}"
        })
        
        # Log final failure
        final_failure = {
            "timestamp": datetime.datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "severity": context.severity.value,
            "recovery_attempted": context.recovery_strategies,
            "final_failure": True
        }
        
        await self.client.call_tool("km_variable_manager", {
            "operation": "set",
            "name": f"CriticalFailure_{int(time.time())}",
            "value": str(final_failure),
            "scope": "global"
        })
        
        print(f"💥 Critical failure logged: {final_failure}")

# Example usage of robust error handling
async def demonstrate_robust_error_handling():
    """Demonstrate comprehensive error handling patterns."""
    
    async with Client("stdio:keyboard-maestro-mcp") as client:
        
        manager = RobustAutomationManager(client)
        
        # Define error context for critical workflow
        critical_context = ErrorContext(
            error_type="workflow_execution",
            severity=ErrorSeverity.HIGH,
            retry_count=0,
            max_retries=3,
            recovery_strategies=["restart_engine", "reset_variables", "restart_applications"],
            metadata={
                "critical_variables": ["WorkflowState", "ProcessingQueue"],
                "target_applications": ["com.microsoft.Word", "com.apple.finder"],
                "temp_paths": ["/tmp/workflow_temp.txt"]
            }
        )
        
        # Define a potentially failing operation
        async def risky_workflow_operation():
            """A workflow operation that might fail."""
            
            # Simulate a workflow that might fail
            result = await client.call_tool("km_execute_macro", {
                "identifier": "Complex Document Workflow",
                "timeout": 60
            })
            
            return result
        
        # Execute with comprehensive error handling
        try:
            result = await manager.execute_with_recovery(
                risky_workflow_operation,
                critical_context
            )
            
            print(f"✅ Workflow completed successfully: {result[0].text}")
            
        except Exception as final_error:
            print(f"💥 Workflow ultimately failed: {final_error}")
            
            # Analyze error patterns for future improvement
            await manager.analyze_error_patterns()

asyncio.run(demonstrate_robust_error_handling())
```

---

## 6. Performance Optimization Examples

### Example 6.1: Batch Operations and Connection Pooling

**Scenario**: Optimize performance for high-volume automation tasks through batching and resource management.

```python
async def optimized_batch_operations():
    """Demonstrate performance optimization techniques for batch operations."""
    
    async with Client("stdio:keyboard-maestro-mcp") as client:
        
        print("⚡ Starting optimized batch operations...")
        
        # Batch 1: Variable Operations (instead of individual calls)
        print("📊 Batch variable operations...")
        
        import time
        start_time = time.time()
        
        # Traditional approach (slow)
        print("🐌 Traditional individual operations...")
        traditional_start = time.time()
        
        for i in range(5):  # Reduced for example
            await client.call_tool("km_variable_manager", {
                "operation": "set",
                "name": f"TestVar_{i}",
                "value": f"Value_{i}",
                "scope": "global"
            })
        
        traditional_time = time.time() - traditional_start
        print(f"📈 Traditional approach: {traditional_time:.2f}s")
        
        # Optimized batch approach
        print("🚀 Optimized batch operations...")
        batch_start = time.time()
        
        # Use dictionary operations for bulk variable management
        variable_batch = {
            f"BatchVar_{i}": f"BatchValue_{i}" 
            for i in range(20)
        }
        
        # Convert to JSON string for bulk operation
        batch_data = str(variable_batch)
        
        # Execute batch variable setting macro
        await client.call_tool("km_execute_macro", {
            "identifier": "Bulk Variable Setter",
            "trigger_value": batch_data,
            "timeout": 30
        })
        
        batch_time = time.time() - batch_start
        print(f"🎯 Batch approach: {batch_time:.2f}s")
        print(f"💡 Performance improvement: {traditional_time/batch_time:.1f}x faster")
        
        # Batch 2: File Operations with Parallel Processing
        print("\n📁 Optimized file operations...")
        
        file_operations = [
            {"source": "/tmp/test1.txt", "dest": "/tmp/backup1.txt"},
            {"source": "/tmp/test2.txt", "dest": "/tmp/backup2.txt"},
            {"source": "/tmp/test3.txt", "dest": "/tmp/backup3.txt"}
        ]
        
        # Create semaphore for controlled concurrency
        semaphore = asyncio.Semaphore(3)  # Limit concurrent operations
        
        async def copy_file_with_limit(operation):
            async with semaphore:
                return await client.call_tool("km_file_operations", {
                    "operation": "copy",
                    "source_path": operation["source"],
                    "destination_path": operation["dest"],
                    "overwrite": True
                })
        
        # Execute file operations concurrently
        parallel_start = time.time()
        
        tasks = [copy_file_with_limit(op) for op in file_operations]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        parallel_time = time.time() - parallel_start
        
        successful_ops = len([r for r in results if not isinstance(r, Exception)])
        print(f"📈 Parallel file operations: {successful_ops}/{len(file_operations)} successful in {parallel_time:.2f}s")
        
        # Batch 3: Macro Execution with Connection Reuse
        print("\n⚙️ Optimized macro execution...")
        
        # Pre-warm the connection and engine
        await client.call_tool("km_engine_status", {
            "operation": "status"
        })
        
        # Execute multiple macros with optimized timing
        macro_execution_start = time.time()
        
        macro_sequence = [
            "Quick Test Macro 1",
            "Quick Test Macro 2", 
            "Quick Test Macro 3"
        ]
        
        # Execute macros with overlapping timing
        macro_tasks = []
        for macro in macro_sequence:
            task = client.call_tool("km_execute_macro", {
                "identifier": macro,
                "timeout": 15
            })
            macro_tasks.append(task)
            
            # Small delay to prevent overwhelming
            await asyncio.sleep(0.1)
        
        # Wait for all macro executions
        macro_results = await asyncio.gather(*macro_tasks, return_exceptions=True)
        
        macro_execution_time = time.time() - macro_execution_start
        successful_macros = len([r for r in macro_results if not isinstance(r, Exception)])
        
        print(f"⚙️ Macro execution: {successful_macros}/{len(macro_sequence)} successful in {macro_execution_time:.2f}s")
        
        # Performance Summary
        total_time = time.time() - start_time
        print(f"\n🏆 Total optimized operations completed in {total_time:.2f}s")
        
        # Save performance metrics
        performance_data = {
            "traditional_time": traditional_time,
            "batch_time": batch_time,
            "parallel_file_time": parallel_time,
            "macro_execution_time": macro_execution_time,
            "total_time": total_time,
            "improvement_factor": traditional_time / batch_time
        }
        
        await client.call_tool("km_variable_manager", {
            "operation": "set",
            "name": "PerformanceMetrics",
            "value": str(performance_data),
            "scope": "global"
        })
        
        print("✅ Performance optimization demonstration completed")

asyncio.run(optimized_batch_operations())
```

### Example 6.2: Resource Management and Caching

**Scenario**: Implement intelligent caching and resource management for frequently accessed operations.

```python
import asyncio
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
import hashlib

@dataclass
class CacheEntry:
    value: Any
    timestamp: float
    ttl: float
    hit_count: int = 0

class IntelligentCachingManager:
    """Intelligent caching system for MCP operations."""
    
    def __init__(self, client, default_ttl: float = 300):  # 5 minutes default TTL
        self.client = client
        self.cache: Dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }
    
    def _generate_cache_key(self, tool_name: str, parameters: Dict) -> str:
        """Generate a unique cache key for the operation."""
        param_str = str(sorted(parameters.items()))
        key_string = f"{tool_name}:{param_str}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _is_cacheable(self, tool_name: str) -> bool:
        """Determine if an operation should be cached."""
        # Only cache read operations and status checks
        cacheable_operations = [
            "km_engine_status",
            "km_list_macros", 
            "km_variable_manager",  # Only for 'get' operations
            "km_app_control"  # Only for status checks
        ]
        return tool_name in cacheable_operations
    
    def _is_cache_valid(self, entry: CacheEntry) -> bool:
        """Check if cache entry is still valid."""
        return (time.time() - entry.timestamp) < entry.ttl
    
    async def cached_call_tool(self, tool_name: str, parameters: Dict, 
                              ttl: Optional[float] = None) -> Any:
        """Execute tool call with intelligent caching."""
        
        # Check if operation is cacheable
        if not self._is_cacheable(tool_name):
            return await self.client.call_tool(tool_name, parameters)
        
        # Special handling for variable manager
        if tool_name == "km_variable_manager" and parameters.get("operation") != "get":
            # Clear related cache entries for set/delete operations
            self._invalidate_variable_cache(parameters.get("name", ""))
            return await self.client.call_tool(tool_name, parameters)
        
        # Generate cache key
        cache_key = self._generate_cache_key(tool_name, parameters)
        
        # Check cache
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if self._is_cache_valid(entry):
                entry.hit_count += 1
                self.stats["hits"] += 1
                print(f"💾 Cache hit for {tool_name} (hits: {entry.hit_count})")
                return entry.value
            else:
                # Remove expired entry
                del self.cache[cache_key]
                self.stats["evictions"] += 1
        
        # Cache miss - execute operation
        self.stats["misses"] += 1
        print(f"🔍 Cache miss for {tool_name} - executing...")
        
        result = await self.client.call_tool(tool_name, parameters)
        
        # Cache the result
        cache_ttl = ttl or self.default_ttl
        self.cache[cache_key] = CacheEntry(
            value=result,
            timestamp=time.time(),
            ttl=cache_ttl
        )
        
        return result
    
    def _invalidate_variable_cache(self, variable_name: str):
        """Invalidate cache entries related to a specific variable."""
        keys_to_remove = []
        for key, entry in self.cache.items():
            if f'"name": "{variable_name}"' in key:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.cache[key]
            self.stats["evictions"] += 1
    
    def get_cache_stats(self) -> Dict:
        """Get cache performance statistics."""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.stats,
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2),
            "cache_size": len(self.cache)
        }
    
    def cleanup_cache(self):
        """Remove expired cache entries."""
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self.cache.items():
            if (current_time - entry.timestamp) >= entry.ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
            self.stats["evictions"] += 1
        
        print(f"🧹 Cleaned up {len(expired_keys)} expired cache entries")

async def demonstrate_caching_performance():
    """Demonstrate intelligent caching for performance optimization."""
    
    async with Client("stdio:keyboard-maestro-mcp") as client:
        
        cache_manager = IntelligentCachingManager(client, default_ttl=60)
        
        print("🧠 Demonstrating intelligent caching...")
        
        # Test 1: Repeated status checks (should be cached)
        print("\n📊 Test 1: Repeated status checks...")
        
        status_start = time.time()
        
        for i in range(5):
            result = await cache_manager.cached_call_tool("km_engine_status", {
                "operation": "status"
            })
            print(f"  Status check {i+1}: {len(result[0].text)} characters")
        
        status_time = time.time() - status_start
        print(f"⏱️ Status checks completed in {status_time:.2f}s")
        
        # Test 2: Variable operations with cache invalidation
        print("\n🔧 Test 2: Variable operations with cache management...")
        
        # Read variable (should be cached)
        var_result1 = await cache_manager.cached_call_tool("km_variable_manager", {
            "operation": "get",
            "name": "TestCacheVar",
            "scope": "global"
        })
        
        # Read same variable again (should hit cache)
        var_result2 = await cache_manager.cached_call_tool("km_variable_manager", {
            "operation": "get", 
            "name": "TestCacheVar",
            "scope": "global"
        })
        
        # Update variable (should invalidate cache)
        await cache_manager.cached_call_tool("km_variable_manager", {
            "operation": "set",
            "name": "TestCacheVar",
            "value": "Updated Value",
            "scope": "global"
        })
        
        # Read variable again (should miss cache due to invalidation)
        var_result3 = await cache_manager.cached_call_tool("km_variable_manager", {
            "operation": "get",
            "name": "TestCacheVar", 
            "scope": "global"
        })
        
        # Test 3: Macro listing with caching
        print("\n📋 Test 3: Macro listing performance...")
        
        list_start = time.time()
        
        # First call (cache miss)
        macros1 = await cache_manager.cached_call_tool("km_list_macros", {
            "include_disabled": True
        })
        
        # Second call (cache hit)
        macros2 = await cache_manager.cached_call_tool("km_list_macros", {
            "include_disabled": True
        })
        
        list_time = time.time() - list_start
        print(f"⏱️ Macro listing completed in {list_time:.2f}s")
        
        # Test 4: Cache cleanup and statistics
        print("\n🧹 Test 4: Cache management...")
        
        # Get initial statistics
        stats = cache_manager.get_cache_stats()
        print(f"📊 Cache statistics: {stats}")
        
        # Perform cache cleanup
        cache_manager.cleanup_cache()
        
        # Final statistics
        final_stats = cache_manager.get_cache_stats()
        print(f"📊 Final cache statistics: {final_stats}")
        
        # Save performance data
        performance_data = {
            "status_check_time": status_time,
            "macro_list_time": list_time,
            "cache_stats": final_stats,
            "cache_hit_rate": final_stats["hit_rate_percent"]
        }
        
        await client.call_tool("km_variable_manager", {
            "operation": "set",
            "name": "CachingPerformanceData",
            "value": str(performance_data),
            "scope": "global"
        })
        
        print(f"🎯 Caching demonstration completed")
        print(f"💡 Cache hit rate: {final_stats['hit_rate_percent']}%")
        print(f"📈 Total requests: {final_stats['total_requests']}")

asyncio.run(demonstrate_caching_performance())
```

---

## 7. Advanced Integration Scenarios

### Example 7.1: AI-Powered Workflow Orchestration

**Scenario**: Advanced AI assistant that can analyze, create, and optimize complex automation workflows.

```python
class AIWorkflowOrchestrator:
    """Advanced AI-powered workflow orchestration system."""
    
    def __init__(self, client):
        self.client = client
        self.workflow_templates = {}
        self.execution_history = []
        self.optimization_rules = []
    
    async def analyze_workflow_requirements(self, user_description: str) -> Dict:
        """Analyze user requirements and suggest optimal workflow structure."""
        
        print(f"🧠 Analyzing workflow requirements: {user_description}")
        
        # In a real implementation, this would use an LLM to analyze requirements
        # For this example, we'll simulate AI analysis
        
        analysis = {
            "workflow_type": "document_processing",
            "complexity": "medium",
            "estimated_steps": 5,
            "required_applications": ["Microsoft Word", "Adobe Acrobat"],
            "data_flow": ["input", "process", "validate", "output", "notify"],
            "optimization_opportunities": [
                "batch_processing",
                "parallel_execution",
                "error_recovery"
            ],
            "risk_factors": ["file_access", "application_availability"]
        }
        
        print(f"📊 Workflow analysis complete: {analysis}")
        return analysis
    
    async def create_adaptive_workflow(self, analysis: Dict, user_preferences: Dict) -> str:
        """Create a workflow that adapts to system conditions and user preferences."""
        
        workflow_id = f"adaptive_workflow_{int(time.time())}"
        
        print(f"🏗️ Creating adaptive workflow: {workflow_id}")
        
        # Step 1: Create workflow tracking group
        await self.client.call_tool("km_manage_macro_group", {
            "operation": "create",
            "properties": {
                "name": f"Adaptive Workflow {workflow_id}",
                "enabled": True,
                "activation_method": "always"
            }
        })
        
        # Step 2: Create main orchestration macro
        orchestration_macro = f"Orchestrate {workflow_id}"
        
        await self.client.call_tool("km_create_macro", {
            "name": orchestration_macro,
            "group_id": f"Adaptive Workflow {workflow_id}",
            "enabled": True,
            "notes": f"AI-generated adaptive workflow for: {analysis['workflow_type']}",
            "triggers": [{
                "type": "hotkey",
                "key": "F12",
                "modifiers": ["Command", "Shift"]
            }]
        })
        
        # Step 3: Create adaptive decision points
        for step_index, step in enumerate(analysis["data_flow"]):
            decision_macro = f"Decision Point {step_index + 1} - {step}"
            
            await self.client.call_tool("km_create_macro", {
                "name": decision_macro,
                "group_id": f"Adaptive Workflow {workflow_id}",
                "enabled": True,
                "notes": f"Adaptive decision point for step: {step}"
            })
        
        # Step 4: Create error recovery macros
        await self.client.call_tool("km_create_macro", {
            "name": f"Error Recovery {workflow_id}",
            "group_id": f"Adaptive Workflow {workflow_id}",
            "enabled": True,
            "notes": "Automated error recovery for workflow failures"
        })
        
        # Step 5: Set up workflow variables
        workflow_config = {
            "workflow_id": workflow_id,
            "user_preferences": user_preferences,
            "analysis_data": analysis,
            "created_timestamp": time.time(),
            "adaptation_enabled": True
        }
        
        await self.client.call_tool("km_variable_manager", {
            "operation": "set",
            "name": f"WorkflowConfig_{workflow_id}",
            "value": str(workflow_config),
            "scope": "global"
        })
        
        print(f"✅ Adaptive workflow created: {workflow_id}")
        return workflow_id
    
    async def execute_with_real_time_adaptation(self, workflow_id: str) -> Dict:
        """Execute workflow with real-time adaptation based on system conditions."""
        
        print(f"🚀 Executing adaptive workflow: {workflow_id}")
        
        execution_log = {
            "workflow_id": workflow_id,
            "start_time": time.time(),
            "adaptations_made": [],
            "performance_metrics": {},
            "completion_status": "in_progress"
        }
        
        try:
            # Step 1: Pre-execution system analysis
            print("🔍 Analyzing system conditions...")
            
            system_conditions = await self._analyze_system_conditions()
            execution_log["system_conditions"] = system_conditions
            
            # Step 2: Adaptive execution strategy selection
            if system_conditions["cpu_load"] > 80:
                execution_log["adaptations_made"].append("Reduced parallel operations due to high CPU")
                parallel_limit = 2
            else:
                parallel_limit = 5
            
            if system_conditions["available_memory"] < 1000:  # MB
                execution_log["adaptations_made"].append("Enabled memory optimization mode")
                memory_optimization = True
            else:
                memory_optimization = False
            
            # Step 3: Execute main workflow with adaptations
            main_execution_start = time.time()
            
            result = await self.client.call_tool("km_execute_macro", {
                "identifier": f"Orchestrate {workflow_id}",
                "trigger_value": f"parallel_limit={parallel_limit};memory_opt={memory_optimization}",
                "timeout": 300
            })
            
            execution_time = time.time() - main_execution_start
            execution_log["performance_metrics"]["main_execution_time"] = execution_time
            
            # Step 4: Post-execution optimization
            if execution_time > 60:  # If execution took longer than expected
                print("⚡ Applying post-execution optimizations...")
                
                await self._optimize_workflow_performance(workflow_id)
                execution_log["adaptations_made"].append("Applied performance optimizations")
            
            # Step 5: Success handling
            execution_log["completion_status"] = "completed"
            execution_log["end_time"] = time.time()
            execution_log["total_execution_time"] = execution_log["end_time"] - execution_log["start_time"]
            
            print(f"✅ Workflow completed in {execution_log['total_execution_time']:.2f}s")
            
        except Exception as e:
            # Adaptive error recovery
            print(f"🔧 Applying adaptive error recovery...")
            
            recovery_success = await self._adaptive_error_recovery(workflow_id, str(e))
            
            if recovery_success:
                execution_log["completion_status"] = "completed_with_recovery"
                execution_log["adaptations_made"].append(f"Recovered from error: {str(e)[:50]}")
            else:
                execution_log["completion_status"] = "failed"
                execution_log["error"] = str(e)
        
        # Save execution log
        await self.client.call_tool("km_variable_manager", {
            "operation": "set",
            "name": f"ExecutionLog_{workflow_id}_{int(time.time())}",
            "value": str(execution_log),
            "scope": "global"
        })
        
        return execution_log
    
    async def _analyze_system_conditions(self) -> Dict:
        """Analyze current system conditions for workflow adaptation."""
        
        conditions = {
            "cpu_load": 45,  # Simulated - would use actual system monitoring
            "available_memory": 2048,  # MB
            "disk_space": 50000,  # MB
            "active_applications": 8,
            "network_connectivity": True,
            "km_engine_responsive": True
        }
        
        # Test actual Keyboard Maestro responsiveness
        try:
            status_start = time.time()
            await self.client.call_tool("km_engine_status", {"operation": "status"})
            response_time = time.time() - status_start
            
            conditions["km_response_time"] = response_time
            conditions["km_engine_responsive"] = response_time < 2.0
            
        except Exception:
            conditions["km_engine_responsive"] = False
            conditions["km_response_time"] = None
        
        return conditions
    
    async def _optimize_workflow_performance(self, workflow_id: str):
        """Apply performance optimizations to workflow."""
        
        # Execute performance optimization macro
        await self.client.call_tool("km_execute_macro", {
            "identifier": "Performance Optimizer",
            "trigger_value": workflow_id,
            "timeout": 60
        })
        
        # Update workflow configuration with optimizations
        optimization_data = {
            "optimization_applied": True,
            "optimization_timestamp": time.time(),
            "optimization_type": "performance_tuning"
        }
        
        await self.client.call_tool("km_variable_manager", {
            "operation": "set",
            "name": f"Optimization_{workflow_id}",
            "value": str(optimization_data),
            "scope": "global"
        })
    
    async def _adaptive_error_recovery(self, workflow_id: str, error_message: str) -> bool:
        """Implement adaptive error recovery strategies."""
        
        try:
            # Execute adaptive error recovery macro
            await self.client.call_tool("km_execute_macro", {
                "identifier": f"Error Recovery {workflow_id}",
                "trigger_value": error_message[:100],  # Pass error context
                "timeout": 120
            })
            
            return True
            
        except Exception as recovery_error:
            print(f"❌ Adaptive recovery failed: {recovery_error}")
            return False

async def demonstrate_ai_workflow_orchestration():
    """Demonstrate advanced AI-powered workflow orchestration."""
    
    async with Client("stdio:keyboard-maestro-mcp") as client:
        
        orchestrator = AIWorkflowOrchestrator(client)
        
        print("🤖 AI Workflow Orchestration Demonstration")
        
        # Step 1: Analyze user requirements
        user_description = """
        I need to automate my daily document review process. 
        Each morning, I receive PDFs via email that need to be:
        1. Downloaded and organized by client
        2. Text extracted and summarized  
        3. Key information added to our project management system
        4. Approval requests sent to team leads
        5. Completed documents archived
        """
        
        analysis = await orchestrator.analyze_workflow_requirements(user_description)
        
        # Step 2: Create adaptive workflow
        user_preferences = {
            "notification_style": "minimal",
            "error_handling": "automatic_retry",
            "performance_priority": "accuracy_over_speed",
            "integration_apps": ["Mail", "Airtable", "Slack"]
        }
        
        workflow_id = await orchestrator.create_adaptive_workflow(analysis, user_preferences)
        
        # Step 3: Execute with real-time adaptation
        execution_result = await orchestrator.execute_with_real_time_adaptation(workflow_id)
        
        # Step 4: Report results
        print(f"\n📊 Execution Summary:")
        print(f"   Status: {execution_result['completion_status']}")
        print(f"   Duration: {execution_result.get('total_execution_time', 0):.2f}s")
        print(f"   Adaptations: {len(execution_result['adaptations_made'])}")
        
        for adaptation in execution_result['adaptations_made']:
            print(f"   • {adaptation}")
        
        # Step 5: Generate insights for future improvements
        insights = {
            "workflow_efficiency": "high" if execution_result.get('total_execution_time', 999) < 60 else "medium",
            "adaptation_effectiveness": len(execution_result['adaptations_made']),
            "recommended_improvements": [
                "Consider pre-caching frequently accessed data",
                "Implement predictive resource allocation",
                "Add more granular error recovery points"
            ]
        }
        
        await client.call_tool("km_variable_manager", {
            "operation": "set",
            "name": f"WorkflowInsights_{workflow_id}",
            "value": str(insights),
            "scope": "global"
        })
        
        print(f"\n💡 AI Insights: {insights}")
        print("✅ AI workflow orchestration demonstration completed")

asyncio.run(demonstrate_ai_workflow_orchestration())
```

## Conclusion

These comprehensive examples demonstrate the full potential of the Keyboard Maestro MCP Server for creating sophisticated, intelligent automation systems. The patterns shown here provide a foundation for building production-ready AI-driven automation solutions that are robust, performant, and adaptable to changing conditions.

**Key Takeaways:**

1. **Error Resilience**: Always implement comprehensive error handling with multiple recovery strategies
2. **Performance Optimization**: Use batching, caching, and parallel processing for high-volume operations  
3. **AI Integration**: Leverage AI for dynamic workflow creation, adaptation, and optimization
4. **System Administration**: Implement monitoring, health checks, and automated maintenance
5. **Context Awareness**: Adapt automation behavior based on current system and user context

**Next Steps:**

- Implement custom error recovery strategies for your specific use cases
- Develop AI integration patterns that match your workflow requirements
- Create performance monitoring dashboards for your automation systems  
- Build comprehensive testing frameworks for complex workflows
- Establish governance and security frameworks for production deployments

For additional examples and advanced patterns, refer to the [TROUBLESHOOTING.md](TROUBLESHOOTING.md) and [CONTRIBUTING.md](CONTRIBUTING.md) guides.
