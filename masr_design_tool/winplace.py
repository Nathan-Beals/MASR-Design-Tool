def get_win_place(win):
    """
    Takes in a window object and returns the position of the master window; this allows for the position of a new
    window to be set in relation to the window it was opened from.
    """
    win.update_idletasks()
    try:
        master_xpos = win.master.master.winfo_rootx()
        master_ypos = win.master.master.winfo_rooty()
        this_xpos = master_xpos
        this_ypos = master_ypos
        return this_xpos, this_ypos
    except AttributeError:
        this_xpos = win.winfo_screenwidth() / 4
        this_ypos = win.winfo_screenheight() / 4
    return this_xpos, this_ypos
