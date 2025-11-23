# UML Diagrams for ApplyChe Project

This directory contains UML diagrams in PlantUML format for the ApplyChe project.

## Files

1. **`database_er.puml`** - Entity Relationship Diagram showing all database tables and their relationships
2. **`api_architecture.puml`** - FastAPI application architecture and component relationships
3. **`class_diagram.puml`** - Class diagrams for existing PyQt6 application code (controllers, models, views)
4. **`sequence_diagrams.puml`** - Sequence diagrams for key workflows (email sending, API requests, dashboard loading)

## Viewing PlantUML Diagrams

### Option 1: VS Code Extension
1. Install the "PlantUML" extension in VS Code
2. Open any `.puml` file
3. Press `Alt+D` (Windows/Linux) or `Option+D` (Mac) to preview

### Option 2: Online Viewer
1. Copy the contents of a `.puml` file
2. Go to http://www.plantuml.com/plantuml/uml/
3. Paste the content and view the diagram

### Option 3: Command Line (Java Required)
```bash
# Install PlantUML
# Download from: http://plantuml.com/download

# Generate PNG
java -jar plantuml.jar database_er.puml

# Generate SVG
java -jar plantuml.jar -tsvg database_er.puml
```

### Option 4: IntelliJ IDEA / PyCharm
1. Install "PlantUML integration" plugin
2. Open `.puml` files directly in the IDE
3. Diagrams render automatically

## Diagram Types

### Entity Relationship Diagram (ERD)
- Shows all 26 database tables
- Displays primary keys (red), foreign keys (blue)
- Shows relationships between tables
- Useful for understanding database schema

### API Architecture Diagram
- Shows FastAPI application structure
- Displays routers, schemas, and database connections
- Color-coded by component type
- Useful for understanding API layer

### Class Diagram
- Shows existing PyQt6 application classes
- Displays attributes and methods
- Shows relationships between classes
- Organized by package (View, Controller, Model, Middleware)

### Sequence Diagrams
- Email sending workflow
- API request flow
- Dashboard data loading
- Shows interaction between components over time

## Integration with Main Documentation

These PlantUML files complement the main `UML_DOCUMENTATION.md` file which contains:
- Mermaid diagrams (for GitHub/GitLab compatibility)
- Detailed explanations
- API endpoint summaries
- Database schema details

## Notes

- PlantUML syntax is case-sensitive
- Use `@startuml` and `@enduml` tags to define diagram boundaries
- Multiple diagrams can be in one file (see `sequence_diagrams.puml`)
- Colors and styling can be customized using PlantUML syntax

## Contributing

When adding new diagrams:
1. Follow the existing naming conventions
2. Include comments explaining complex relationships
3. Update this README if adding new diagram types
4. Test diagrams in at least one viewer before committing

