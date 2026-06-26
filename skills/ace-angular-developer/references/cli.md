# Angular CLI Guide for Agents

The Angular CLI (`ng`) is the primary tool for managing an Angular workspace. Always prefer CLI commands over manual file creation or generic `npm` commands when modifying project structure or adding Angular-specific dependencies.

## 1. Managing Dependencies

To update the application and its dependencies (which automatically runs code migrations):

```bash
ng update @angular/core@<latest or specific version> @angular/cli<latest or specific version>
```

## 2. Generating Code (`ng generate` or `ng g`)

Always use the CLI to generate code to ensure it adheres to Angular standards and updates necessary configuration files automatically.

| Target       | Command               | Notes                                                                                          |
| :----------- | :-------------------- | :--------------------------------------------------------------------------------------------- |
| Component    | `ng g c path/to/name` | Generates a component. Use `--inline-style` (`-s`) or `--inline-template` (`-t`) if requested. |
| Service      | `ng g s path/to/name` | Generates an `@Injectable({providedIn: 'root'})` service.                                      |
| Directive    | `ng g d path/to/name` | Generates a directive.                                                                         |
| Pipe         | `ng g p path/to/name` | Generates a pipe.                                                                              |
| Guard        | `ng g g path/to/name` | Generates a functional route guard.                                                            |
| Environments | `ng g environments`   | Scaffolds `src/environments/` and updates `angular.json` with file replacements.               |

_Note: There is no command to generate a single route definition. Generate a component, then manually add it to the `Routes` array in `app.routes.ts`._

## 3. Development Server

To start the application use the ace-start-application skill

## 4. Building the Application

Compile the application into an output directory (default: `dist/<project-name>/browser`). Modern Angular uses the `@angular/build:application` builder (esbuild-based).

```bash
ng build
```

- `ng build` defaults to the production configuration, which enables Ahead-of-Time (AOT) compilation, minification, and tree-shaking.
- Target specific configurations defined in `angular.json` using `--configuration`: `ng build --configuration=staging`.

## 5. Testing

- **Unit Tests**: Run `pnpm test` to execute unit tests via Jest.
- **Component tests**: Run `pnpm component-tests`.
