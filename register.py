import argparse
import os
from context_menu import menus


MENU_NAME = r'Patrol Source Utility'
MENU_TYPE = r"DIRECTORY"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=f'Un/Register {MENU_NAME}')
    parser.add_argument('-r', '--revert', default=False,
                        action="store_true", help='Revert registration')
    args = parser.parse_args()
    if args.revert:
        menus.removeMenu(MENU_NAME, type=MENU_TYPE)
        print(f"[CONTEXT_MENU] Unregistered option {MENU_NAME}")
    else:
        cmd_path = os.path.abspath("launch.cmd")
        this_dir = os.path.abspath(".")

        cm = menus.ContextMenu(MENU_NAME, type=MENU_TYPE)
        cm.add_items([
            menus.ContextCommand(
                'Write to HTML', f'"{cmd_path}" "%1" "-ohtml" "" "{this_dir}"'),
            menus.ContextCommand(
                'Write to JSON', f'"{cmd_path}" "%1" "-ojson" "" "{this_dir}"')
        ])

        cm.compile()
        print(f"[CONTEXT_MENU] Registered option {MENU_NAME}")
