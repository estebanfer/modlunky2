import json
import logging
import shutil
import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk

from modlunky2.utils import open_directory


logger = logging.getLogger("modlunky2")


class Pack:
    def __init__(self, play_tab, parent, modlunky_config, folder):
        self.play_tab = play_tab
        self.modlunky_config = modlunky_config
        self.folder = folder
        self.needs_update = False

        self.pack_metadata_path = (
            modlunky_config.install_dir / "Mods/.ml/pack-metadata" / folder
        )
        self.manifest_path = self.pack_metadata_path / "manifest.json"

        self.manifest = {}
        self.logo_img = None
        self.name = folder

        self.logo = ttk.Label(parent)
        self.var = tk.BooleanVar()
        self.checkbutton = ttk.Checkbutton(
            parent,
            text=self.name,
            style="ModList.TCheckbutton",
            variable=self.var,
            onvalue=True,
            offvalue=False,
            compound="left",
            command=self.on_check,
        )

        button_padding = 1
        self.buttons = ttk.Frame(parent)
        self.buttons.rowconfigure(0, weight=1)

        self.buttons.update_button = ttk.Button(
            self.buttons,
            padding=button_padding,
            image=self.play_tab.update_icon,
            command=self.open_pack_dir,
        )

        self.buttons.options_button = ttk.Button(
            self.buttons,
            padding=button_padding,
            image=self.play_tab.options_icon,
            command=self.open_pack_dir,
        )
        # self.buttons.options_button.grid(row=0, column=1, padx=(1, 0), sticky="e")

        self.buttons.folder_button = ttk.Button(
            self.buttons,
            padding=button_padding,
            image=self.play_tab.folder_icon,
            command=self.open_pack_dir,
        )
        self.buttons.folder_button.grid(row=0, column=2, padx=(1, 0), sticky="e")

        self.buttons.trash_button = ttk.Button(
            self.buttons,
            padding=button_padding,
            image=self.play_tab.trash_icon,
            command=self.remove_pack,
        )
        self.buttons.trash_button.grid(row=0, column=3, padx=(1, 0), sticky="e")
        self.on_load()

    def on_load(self):
        if self.manifest_path.exists():
            with self.manifest_path.open("r", encoding="utf-8") as manifest_file:
                self.manifest = json.load(manifest_file)
        else:
            self.manifest = {}

        self.name = self.manifest.get("name", self.folder)
        self.checkbutton.configure(text=self.name)
        if (
            self.manifest.get("logo")
            and (self.pack_metadata_path / self.manifest["logo"]).exists()
        ):
            self.logo_img = ImageTk.PhotoImage(
                Image.open(self.pack_metadata_path / self.manifest["logo"]).resize(
                    (40, 40), Image.ANTIALIAS
                )
            )
            self.logo.configure(image=self.logo_img)
        else:
            self.logo_img = None
            self.logo.configure(image=None)

    def forget(self):
        self.logo.grid_forget()
        self.checkbutton.grid_forget()
        self.buttons.grid_forget()

    def grid(self, row):
        self.logo.grid(row=row, column=0, sticky="ew")
        self.checkbutton.grid(row=row, column=1, pady=0, padx=5, sticky="nsw")
        self.buttons.grid(row=row, column=2, pady=0, padx=(5, 25), sticky="e")

    def render_buttons(self):
        if not (self.modlunky_config.install_dir / "Mods/Packs" / self.folder).exists():
            self.buttons.folder_button["state"] = tk.DISABLED
        else:
            self.buttons.folder_button["state"] = tk.NORMAL

        if self.needs_update:
            self.buttons.update_button.grid(row=0, column=0, padx=(1, 0), sticky="e")
        else:
            self.buttons.update_button.grid_forget()

    def selected(self):
        return self.var.get()

    def enable(self):
        self.var.set(True)

    def disable(self):
        self.var.set(False)

    def set(self, val: bool):
        if val:
            self.enable()
        else:
            self.disable()
        self.on_check()

    def destroy(self):
        self.checkbutton.destroy()
        self.buttons.destroy()
        self.logo.destroy()
        self.play_tab.load_order.delete(self.folder)

    def on_check(self):
        if self.var.get():
            self.play_tab.load_order.insert(self.folder)
        else:
            self.play_tab.load_order.delete(self.folder)
        self.play_tab.render_packs()

    def open_pack_dir(self):
        if self.folder.startswith("/"):
            logger.warning("Got dangerous pack name, aborting...")
            return

        pack_dir = self.modlunky_config.install_dir / "Mods/Packs" / self.folder
        if not pack_dir.exists():
            logger.info("No pack directory found to remove. Looked in %s", pack_dir)
            return

        open_directory(pack_dir)

    def remove_pack(self):
        if self.folder.startswith("/"):
            logger.warning("Got dangerous pack name, aborting...")
            return

        to_remove = []
        pack_dir = self.modlunky_config.install_dir / "Mods/Packs" / self.folder
        if pack_dir.exists():
            to_remove.append(pack_dir)

        if not to_remove:
            logger.info("No pack directory found to remove. Looked in %s", pack_dir)

        removing = "\n".join(map(str, to_remove))
        answer = tk.messagebox.askokcancel(
            title="Confirmation",
            message=(
                "Are you sure you want to remove this pack?\n"
                "\n"
                "This will remove the following:\n"
                f"{removing}"
            ),
            icon=tk.messagebox.WARNING,
        )

        if not answer:
            return

        for path in to_remove:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
        self.play_tab.on_load()