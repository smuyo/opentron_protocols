import copy

od_csv = [[0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15],
[0.91,0.893,0.86,0.724,0.699,0.69,0.566,0.469,0.349,0.196,0.096,0.091],
[0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15],
[0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15],
[0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15],
[0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15],
[0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15],
[0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15]]
target_od = 0.15
top_od = 0.2
initial_volume = 150
target_volume = 150
vol_well = 300

metadata = {
    'apiLevel' : '2.11',
    'protocolName' : 'OD Normalization',
    'author' : 'Sergi Muyo <sergimuyo@gmail.com',
    'description' : 'Produce a 96-well plate with a target OD'
}

def calculate_OD(initial_OD, final_OD, final_volume, start_volume, max_intermediate, max_od):
    out_vols = []
    subpart = round((final_OD * final_volume) / initial_OD)
    aspir_vol = start_volume - subpart
    if aspir_vol <= 0:
        return out_vols
    if aspir_vol <= start_volume - 50:
        out_vols.append(aspir_vol)
        if start_volume > final_volume:
            aspir_vol2 = final_volume - (start_volume - aspir_vol)
        elif start_volume == final_volume:
            aspir_vol2 = aspir_vol
        else:
            aspir_vol2 = final_volume - (start_volume - aspir_vol)
        out_vols.append(aspir_vol2)
    else:
        first_aspir = start_volume - 50
        out_vols.append(first_aspir)
        volume_need = round((50 * initial_OD) / final_OD)
        if volume_need <= max_intermediate:
            media_vol = volume_need - 50
            out_vols.append(media_vol)
            well_out = volume_need - final_volume
            out_vols.append(well_out)
        else:
            media_vol = max_intermediate - 50
            out_vols.append(media_vol)
            new_OD = (50 * initial_OD) / max_intermediate
            if new_OD < max_od:
                out_vols.append(max_intermediate - final_volume)
            else:
                second_vols = calculate_OD(new_OD, final_OD, final_volume, max_intermediate, max_intermediate, max_od)
                for volume in second_vols:
                    out_vols.append(volume)
    return out_vols

def custom_mix(times, pipette, location, volums):
    for i in range(times):
        pipette.aspirate(volums, location)
        pipette.dispense(volums, location, rate=3.33)

def run(protocol):
    reservoir = protocol.load_labware('opentrons_6_tuberack_falcon_50ml_conical', 6)
    source = reservoir.wells()[0].top(z=-36)
    tr_tube = reservoir.wells()[5].top(z=-14)

    tiprack_1 = protocol.load_labware('opentrons_96_tiprack_300ul', 2)
    tiprack_2 = protocol.load_labware('opentrons_96_tiprack_300ul', 5)
    tiprack_3 = protocol.load_labware('opentrons_96_tiprack_300ul', 1)

    wellplate = protocol.load_labware('corning_96_wellplate_360ul_flat', 3)

    l_pip = protocol.load_instrument('p300_single', 'left', [tiprack_1, tiprack_2, tiprack_3])

    source_dirs = []
    dest_dirs = []

    wp_rows = wellplate.rows()
    vols_transfer = []
    media_vols = []

    z_pos = -36
    used_vol = 0
    max_vol = 5000
    for row_num in range(len(od_csv)):
        if used_vol >= max_vol:
            z_pos -= 9
            max_vol += 5000
            source = reservoir.wells()[0].top(z=z_pos)
        for col_num in range(len(od_csv[row_num])):
            if od_csv[row_num][col_num] <= target_od:
                continue
            volumes = calculate_OD(od_csv[row_num][col_num], target_od, target_volume, initial_volume, vol_well, top_od)
            for vol_num in range(len(volumes)):
                used_vol += volumes[vol_num]
                vols_transfer.append(volumes[vol_num])
                if vol_num%2 == 0:
                    source_dirs.append(wp_rows[row_num][col_num])
                    dest_dirs.append(tr_tube)
                else:
                    source_dirs.append(source)
                    dest_dirs.append(wp_rows[row_num][col_num])

    mix_volume = round(target_volume / 3)

    for instru in range(len(vols_transfer)):
        curr_vol = vols_transfer[instru]
        curr_source = source_dirs[instru]
        curr_dest = dest_dirs[instru]
        if past_dest != curr_source:
            if l_pip.has_tip:
                l_pip.drop_tip()
        if curr_source == source:
            if not l_pip.has_tip:
                l_pip.pick_up_tip()
            l_pip.transfer(curr_vol, curr_source, curr_dest, new_tip='never')
        else:
            if not l_pip.has_tip:
                l_pip.pick_up_tip()
            custom_mix(5, l_pip, curr_source, 100)
            l_pip.transfer(curr_vol, curr_source, curr_dest, new_tip='never')
            l_pip.drop_tip()
        past_dest = copy.deepcopy(curr_dest)
