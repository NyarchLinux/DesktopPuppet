# DesktopPuppet
Acchan on the desktop yeahhh.

> [!WARNING]
> This is still in early alpha. Some features are still missing and only Hyprland is supported for now.

## Supported Desktops

- [x] Hyprland
- [ ] KDE
- [ ] Sway
- [ ] Cosmic
- [ ] Gnome (* Gnome does not support GTK layer shell so it's going a bit painful)

## Installation
1. `gtk4-layer-shell` is required, you can install it on arch using

```bash
sudo pacman -S gtk4-layer-shell
```

2. Be sure to have these dependencies available:
```bash
sudo pacman -S python-requests python-gobject
```

3. Download Nyarch Assistant
4. Download our Nyarch Assistant extension
5. Go in Nyarch Assistant settings, scroll to avatar, click on the download button near desktop pet option, and wait for it to finish, then select it. 
6. Hope that it doesn't explode

## Hyprland Suggestions
### Keybinds
You can set these keybinds to control the desktop pet

```hyprlang
bind = SUPER, F7, exec, $HOME/.var/app/moe.nyarchlinux.assistant/config/avatars/live2d/DesktopPuppet/src/cli.sh set-overlay background
bind = SUPER, F8, exec, $HOME/.var/app/moe.nyarchlinux.assistant/config/avatars/live2d/DesktopPuppet/src/cli.sh set-overlay overlay
bind = SUPER, F10, sendshortcut, Control_L, s, title:nyarchassistant
bind = SUPER, F9, sendshortcut, Control_L, k, title:nyarchassistant
```

`SUPER+F7` -> Put the pet in the background

`SUPER+F8` -> Put the per on the window

`SUPER+F9` -> Stop TTS from playing

`SUPER+F10` -> Start recording with microphone
