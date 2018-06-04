from upload import VolUpload

parameters = {
    "mult_chan_stacks": ["Take2Site4Align_Session1",
                         "Take2Site4Align_Session2",
                         "Take2Site4Align_Session3"],
    "volume_name": "Take2Site4",
    "regular_stacks": ["Take2Site4Align_EMclahe"],
    "regular_stacks_names": ["EM"],
    "render": {
        "host": "http://ibs-forrestc-ux1.corp.alleninstitute.org",
        "port": "80",
        "owner": "Forrest",
        "project": "M247514_Rorb_1"
    }
}

mod = VolUpload(input_data=parameters, args=[])
mod.run()
