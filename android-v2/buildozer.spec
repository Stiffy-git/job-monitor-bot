[app]

title = Job Monitor Bot
package.name = jobmonitor
package.domain = com.jobmonitor

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 2.0

requirements = python3,kivy,aiohttp

orientation = portrait

fullscreen = 0

android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

android.api = 31
android.minapi = 21
android.ndk = 25b

android.accept_sdk_license = True

android.archs = arm64-v8a

log_level = 2
