plugins {
    id("org.jetbrains.intellij.platform") version "2.19.0"
}

group = "dev.danvega"
version = providers.gradleProperty("pluginVersion").get()

repositories {
    mavenCentral()
    intellijPlatform {
        defaultRepositories()
    }
}

dependencies {
    intellijPlatform {
        val localIde = providers.gradleProperty("localIdePath")
        if (localIde.isPresent) {
            local(localIde)
        } else {
            intellijIdea(providers.gradleProperty("platformVersion"))
        }
    }
}

intellijPlatform {
    // A theme plugin has no code and no settings pages.
    buildSearchableOptions = false
    instrumentCode = false

    pluginConfiguration {
        ideaVersion {
            // 2026.2 is the first release with the Islands color tokens the themes override.
            sinceBuild = "262"
            untilBuild = provider { null }
        }
    }
}

tasks.runIde {
    // Open the sample project and file so every syntax color is on screen.
    val samples = layout.projectDirectory.dir("samples")
    args(
        samples.asFile.absolutePath,
        samples.file("src/dev/danvega/todos/TodoService.java").asFile.absolutePath,
    )
}

tasks.register<Exec>("generateThemes") {
    group = "kiln"
    description = "Regenerates the theme files from the palettes in scripts/generate_themes.py."
    commandLine("python3", "scripts/generate_themes.py", intellijPlatform.platformPath.toString())
}
