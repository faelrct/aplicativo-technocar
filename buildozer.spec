[app]
title = Techno Car
package.name = technocar
package.domain = org.faeldograu
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json
version = 0.1
requirements = python3,kivy,pillow
orientation = portrait
fullscreen = 0

# Android config
android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1