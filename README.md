# Kiln Theme for IntelliJ

A warm dark and light theme for JetBrains IDEs. It uses charcoal and cream surfaces, a clay orange accent, and calm, earthy syntax colors. Each variant recolors the whole IDE, the editor, and the terminal.

![Kiln Dark](images/screenshot-dark.jpg)

![Kiln Light](images/screenshot-light.jpg)

## Tested with

IntelliJ IDEA 2026.2.3, Gradle 9.8.1, IntelliJ Platform Gradle Plugin 2.19.0, Java 26.

The plugin supports IntelliJ-based IDEs 2025.3 and newer.

## What you need

- A JDK 17 or newer to run Gradle.
- IntelliJ IDEA 2025.3 or newer.
- Python 3, only if you want to change the colors.

## Build and install

```bash
./gradlew buildPlugin
```

This writes `build/distributions/kiln-theme-1.0.0.zip`. In IntelliJ, open **Settings | Plugins**, click the gear icon, and choose **Install Plugin from Disk**. Then pick **Kiln Dark** or **Kiln Light** in **Settings | Appearance & Behavior | Appearance | Theme**.

By default the build downloads IntelliJ IDEA 2025.3 to compile against. To use the IDE you already have, pass its path:

```bash
./gradlew buildPlugin -PlocalIdePath="/Applications/IntelliJ IDEA.app"
```

## Try it in a sandbox IDE

```bash
./gradlew runIde -PlocalIdePath="/Applications/IntelliJ IDEA.app"
```

This starts a separate IDE with the plugin installed and opens [samples/src/dev/danvega/todos/TodoService.java](samples/src/dev/danvega/todos/TodoService.java). The sample has keywords, strings, annotations, fields, constants, Javadoc, a TODO, a warning, and an error, so most syntax colors are on screen at once.

## Change the colors

The palettes live in [scripts/generate_themes.py](scripts/generate_themes.py). Edit the `DARK` or `LIGHT` dictionary, then regenerate the theme files:

```bash
python3 scripts/generate_themes.py "/Applications/IntelliJ IDEA.app"
```

The script rewrites the four files in [src/main/resources/themes](src/main/resources/themes). It also prints the contrast ratio of each syntax color against the editor background.

To try palette ideas before touching the plugin, open [preview/mockup.html](preview/mockup.html) in a browser. It is a mock IDE window with a color picker for every token.

## Good to know

- Both themes inherit from the Islands themes (`Islands Dark` and `Islands Light`), the default look since 2025.3. That is why older IDE versions are not supported.
- The Islands themes resolve their own named colors before a child theme's colors apply. Overriding one token, such as `accent-brand-bg`, does not reach the keys that point at it through another name. So the generator reads every Islands token from your IDE, resolves it through the Kiln palette, and writes all of them out as hex values. Do not hand-edit the generated `.theme.json` files.
- The editor schemes use Darcula and Default as their parents. Darcula sets some Java and Kotlin keys directly, so the schemes set those keys too, not only the `DEFAULT_*` ones.
