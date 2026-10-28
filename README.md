# DesktopPuppet
Acchan on the desktop yeahhh.

You can check out our video for installation.

[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/exlC3R4hj8w/0.jpg)](https://www.youtube.com/watch?v=exlC3R4hj8w)


> [!WARNING]
> This is still in beta. Some features are still missing and only Hyprland is fully supported for now. KDE and Gnome are in a beta stage

## Supported Desktops

- [x] Hyprland
- [x] KDE
    - [x] Pointer focusing 
    - [ ] Get correct monitor resolution
    - [ ] Set correct window size
- [ ] Sway
- [ ] Cosmic
- [x] Gnome (* Still requires some work, requires a Shell extension, download instructions at the bottom)
  - [x] Pointer focusing
  - [x] Start as always on top
  - [x] Get correct monitor resolution
  - [x] Set correct window size
  - [x] Set it visible on every desktop
  - [x] Overlay/Background switch

## Installation

DesktopPuppet needs a Wayland compositor that supports layer shell, plus Python 3.10 or newer, `git`, and these packages:

```bash
sudo pacman -S python-requests python-gobject webkitgtk-6.0 libadwaita gtk4-layer-shell
```

On KDE, also install [Kdotool](https://github.com/jinliu/kdotool). On Arch:

```bash
yay -S kdotool-git
```

On GNOME, install the Shell extension described in [Gnome Specific Instructions](#gnome-specific-instructions) before starting the pet.

The first `start` clones the [Live2D viewer](https://github.com/NyarchLinux/live2d-lipsync-viewer) and its default Arch model. A writable checkout gets `avatars/live2d/web`; a system install gets `~/.local/share/desktoppuppet/live2d/web`.

### From the install script

Clone the repository, then install it. Writing to `/usr` needs root; a user install does not.

```bash
git clone https://github.com/NyarchLinux/DesktopPuppet.git
cd DesktopPuppet
sudo ./install.sh
```

Install only for your user with:

```bash
PREFIX="$HOME/.local" ./install.sh
```

Make sure `$HOME/.local/bin` is on your `PATH`. Skip the Arch package check with `--skip-deps` if the dependencies are already installed under different package names.

Then start the pet, or open the controller:

```bash
desktoppuppet start
desktoppuppet gui
```

Remove a system install with `sudo ./install.sh --uninstall`. For a user install, pass the same prefix: `PREFIX="$HOME/.local" ./install.sh --uninstall`.

### From the Arch package

The included `PKGBUILD` builds from the `0.1.0` tag:

```bash
makepkg -si
```

### From the source tree

Dependencies are the same as above. No install step is required:

```bash
git clone https://github.com/NyarchLinux/DesktopPuppet.git
cd DesktopPuppet
python3 src/cli.sh start
```

Open the controller with `./run_gui.sh`.

### From Nyarch Assistant

1. Download Nyarch Assistant.
2. Download the Nyarch Assistant extension.
3. Open Nyarch Assistant settings, scroll to avatar, and click the download button next to the desktop pet option.
4. Wait for the download to finish, then select the pet.

## Gnome Specific Instructions
Gnome is in an early support stage, a few features are still missing but it's usable.
It is required to install the [Nyarch Pet Extension](https://github.com/NyarchLinux/NyarchPetGnomeExtension/).
You can do it in one command:
```
git clone https://github.com/NyarchLinux/NyarchPetGnomeExtension/ ~/.local/share/gnome-shell/extensions/nyarchpet@nyarchlinux.moe
```
Then log out and back in, or enable it in the running session as described below.
Additional instructions:
- The pet opens on the monitor under the pointer and fills its work area. You can pick a fixed monitor in the controller or with `--monitor` (see below), or in the extension preferences. The controller and `--monitor` need the extension from this repository, which adds the `SetMonitor` D-Bus method
- Background mode keeps the pet below other windows, not behind the desktop icons, because GNOME has no wallpaper layer for apps. Clicking the pet can bring it forward for a moment before it drops back

### Enable the extension without logging out
GNOME Shell only scans the extensions folder at login, so it does not see a newly installed extension right away. You can load it into the running session with Looking Glass:

1. Press `Alt+F2`, type `lg` and press Enter.
2. Paste this line into the Evaluator tab and press Enter:
```js
const uuid = 'nyarchpet@nyarchlinux.moe'; const dir = Gio.File.new_for_path(GLib.get_user_data_dir() + '/gnome-shell/extensions/' + uuid); await Main.extensionManager.loadExtension(Main.extensionManager.createExtensionObject(uuid, dir, 2)); Main.extensionManager.enableExtension(uuid)
```
3. Press `Esc` to close Looking Glass, then check that the state is `ACTIVE`:
```bash
gnome-extensions info nyarchpet@nyarchlinux.moe
```

If the extension was already installed when you logged in and is just disabled, `gnome-extensions enable nyarchpet@nyarchlinux.moe` is enough.

GNOME Shell loads the code of an extension only once per session. If any version of the extension has already run in the current session, you still need to log out to use an updated version. To test changes without logging out, start a nested shell with `dbus-run-session gnome-shell --devkit` (GNOME 49 and later) or `dbus-run-session gnome-shell --nested --wayland` (GNOME 47 and 48).

## KDE Specific Instructions

KDE support needs [Kdotool](https://github.com/jinliu/kdotool), installed as described above.


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

## GUI Control

A GTK4 + Libadwaita GUI is available to control the desktop puppet with a modern web-designed interface.

Run the GUI with:
```bash
./run_gui.sh
```

Or directly:
```bash
python3 src/gui_controller.py
```

### Choosing a monitor

Pick a monitor in the **Monitor** row of the controller before launching. **Automatic** uses the focused monitor. From the command line, pass the monitor connector name:

```bash
python3 src/cli.sh start --monitor DP-1
```

The controller shows each connector name next to the monitor model. On Hyprland, `hyprctl monitors` lists them too.
