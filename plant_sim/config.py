# config.py ----------------------------------------------------------
SIM_TIME =     10000
INTERARRIVAL = 0

# DICTIONARIES 

network = {
    'SAW1': { #OP10A
        'process_time': 6.62,
        'OEE': 0.8313,      
        'output': 'WIPo_SAW1' # machine outputs into a WIP area node 
    },
    'WIPo_SAW1': {
        'next': ['WIPi_IH1', 'WIPi_IH2'],
        'transport_times': [1.0482, 1.0482]
    },
    'SAW2': {
        'process_time': 6.62,
        'OEE': 0.8313,
        'output': 'WIPo_SAW2'
    },
    'WIPo_SAW2': {
        'next': ['WIPi_IH1', 'WIPi_IH2'],
        'transport_times': [1.0482, 1.0482]
    },
    'SAW3': { #OP10B
        'process_time': 12.53,
        'OEE': 0.8313,
        'output': 'WIPo_SAW3' # machine outputs into a WIP area node 
    },
    'WIPo_SAW3': {
        'next': ['WIPi_IH3'],
        'transport_times': [1.0482, 1.0482]
    },
    'SAW4': {
        'process_time': 6.62,
        'OEE': 0.8313,
        'output': 'WIPo_SAW4'
    },
    'WIPo_SAW4': {
        'next': ['WIPi_IH3'],
        'transport_times': [1.0482]
    },
    'SAW5': { # extra machine 
        'process_time': 12.15,
        'OEE': 0,
        'output': 'WIPo_SAW5'
    },
    'WIPo_SAW5': {
        'next': ['WIPi_IH3'],
        'transport_times': [1.0482]
    },
    'SAW6': { #OP10A
        'process_time': 6.62,
        'OEE': 0,      
        'output': 'WIPo_SAW6' # machine outputs into a WIP area node 
    },
    'WIPo_SAW6': {
        'next': ['WIPi_IH1', 'WIPi_IH2'],
        'transport_times': [1.0482, 1.0482]
    },
    'SAW7': {
        'process_time': 6.46,
        'OEE': 0,
        'output': 'WIPo_SAW7'
    },
    'WIPo_SAW7': {
        'next': ['WIPi_IH3'],
        'transport_times': [1.0482, 1.0482]
    },
    'SAW8': { #OP10B
        'process_time': 12.53,
        'OEE': 0,
        'output': 'WIPo_SAW8' # machine outputs into a WIP area node 
    },
    'WIPo_SAW8': {
        'next': ['WIPi_IH1', 'WIPi_IH2'],
        'transport_times': [1.0482, 1.0482]
    },
    'SAW9': {
        'process_time': 12.15,
        'OEE': 0,
        'output': 'WIPo_SAW9'
    },
    'WIPo_SAW9': {
        'next': ['WIPi_IH3'],
        'transport_times': [1.0482]
    },
    'WIPi_IH1': {
        'next': ['IH1'],
        'transport_times': 0
    },
    'WIPi_IH2': {
        'next': ['IH2'],
        'transport_times': 0
    },
    'IH1': {
        'process_time': 3.78,
        'OEE': 0.85,
        'output': 'P1'
    },
    'IH2': {
        'process_time': 3.78,
        'OEE': 0,   #0.85
        'output': 'P1'
    },
    'P1': {
        'process_time': 2.54,
        'OEE': 0.85,                     #0.4259
        'output': 'storage_after_press'
    },
    'WIPi_IH3': {
        'next': ['IH3'],
        'transport_times': 0
    },
    'IH3': {
        'process_time': 3.78,
        'OEE': 0.85,
        'output': 'P2'
    },
    'P2': {
        'process_time': 3.67,
        'OEE': 0.85,                    #0.4259
        'output': 'storage_after_press'
    },
    'storage_after_press': {
        'next': ['CL1', 'CL2', 'CL3', 'CL4'],
        'transport_times': [1.2114, 1.2114, 1.2114, 1.2114]
    },
    'CL1': {
        'process_time': 9.36,
        'OEE': 0.8050,
        'output': 'WIPo_CL'
    },
    'CL2': {
        'process_time': 7.23,
        'OEE': 0.8050,
        'output': 'WIPo_CL'        
    },
    'CL3': {
        'process_time': 8.02,
        'OEE': 0.8050,
        'output': 'WIPo_CL'         
    },
    'CL4': {
        'process_time': 7.23,
        'OEE': 0.8050,
        'output': 'WIPo_CL'         
    },
    'CL5': {
        'process_time': 9.36,
        'OEE': 0,
        'output': 'WIPo_CL'
    },
    'CL6': {
        'process_time': 7.23,
        'OEE': 0,
        'output': 'WIPo_CL'        
    },
    'CL7': {
        'process_time': 8.02,
        'OEE': 0,
        'output': 'WIPo_CL'         
    },
    'CL8': {
        'process_time': 7.23,
        'OEE': 0,
        'output': 'WIPo_CL'         
    },
    'WIPo_CL': {
        # send cooled shells to all four SB buffers
        'next': ['WIPi_CC1', 'WIPi_CC2', 'WIPi_CC3', 'WIPi_CC4'],
        'transport_times': [1.8130, 1.8130, 1.8130, 1.8130]
    },
#     'WIPo_CL': {
#         # send cooled shells to all four SB buffers
#         'next': ['finished_goods'],
#         'transport_times': [1.8130]
#     },

    # each buffer feeds its own SB machine
    'WIPi_CC1': { 
        'next': ['CC1'], 
        'transport_times': 0 
    },
    'WIPi_CC2': { 
        'next': ['CC2'], 
        'transport_times': 0 
    },
    'WIPi_CC3': { 
        'next': ['CC3'], 
        'transport_times': 0 
    },
    'WIPi_CC4': { 
        'next': ['CC4'], 
        'transport_times': 0 
    },

    # SB machines
    'CC1': { 
        'process_time': 2.41, 
        'OEE': 0.8330, 
        'output': 'WIPo_CC1' 
    },
    'CC2': { 
        'process_time': 2.41, 
        'OEE': 0.8330, 
        'output': 'WIPo_CC2' 
    },
    'CC3': { 
        'process_time': 2.41, 
        'OEE': 0, 
        'output': 'WIPo_CC3' 
    },
    'CC4': { 
        'process_time': 2.41, 
        'OEE': 0, 
        'output': 'WIPo_CC4' 
    },

    # SB outputs palletise to finished goods
    'WIPo_CC1': { 
        'next': ['finished_goods'], 
        'transport_times': 1.8130 
    },
    'WIPo_CC2': { 
        'next': ['finished_goods'], 
        'transport_times': 1.8130 
    },
    'WIPo_CC3': { 
        'next': ['finished_goods'], 
        'transport_times': 1.8130 
    },
    'WIPo_CC4': { 
        'next': ['finished_goods'], 
        'transport_times': 1.8130 
    },
    'finished_goods': {
        'next': ['WIPo_GantryIn'],
        'transport_times': 1.8130 
    },
    'WIPo_GantryIn': {
        'next': ['WIPo_GantryConv'],
        'transport_times': 0.25
    },
    'WIPo_GantryConv': {
        'next': ['WIPi_ROD'],
        'transport_times': 0.25   
    },
    'WIPi_ROD': {
        'next': ['ROD1', 'ROD2', 'ROD3', 'ROD4', 'ROD5', 'ROD6', 'ROD7', 'ROD8', 'ROD9', 'ROD10'],   #ended mc update here 
        'transport_times': [2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5]
    },
    'ROD1': {
        'process_time': 11.26,
        'OEE': 0.4242,
        'output': 'WIPo_ROD1'        
    },
    'ROD2': {
        'process_time': 11.38,
        'OEE': 0.4242,
        'output': 'WIPo_ROD2'         
    },
    'ROD3': {
        'process_time': 11.26,
        'OEE': 0.4242,
        'output': 'WIPo_ROD3' 
    },
    'ROD4': {
        'process_time': 11.38,
        'OEE': 0.4242,
        'output': 'WIPo_ROD4' 
    },
    'ROD5': {
        'process_time': 11.26,
        'OEE': 0.4242,
        'output': 'WIPo_ROD5' 
    },
    'ROD6': {
        'process_time': 11.26,
        'OEE': 0,
        'output': 'WIPo_ROD6'        
    },
    'ROD7': {
        'process_time': 11.38,
        'OEE': 0,
        'output': 'WIPo_ROD7'         
    },
    'ROD8': {
        'process_time': 11.26,
        'OEE': 0,
        'output': 'WIPo_ROD8' 
    },
    'ROD9': {
        'process_time': 11.38,
        'OEE': 0,
        'output': 'WIPo_ROD9' 
    },
    'ROD10': {
        'process_time': 11.26,
        'OEE': 0,
        'output': 'WIPo_ROD10' 
    },
    'WIPo_ROD1': {
        'next': ['WIPi_RID1', 'WIPi_RID2', 'WIPi_RID3','WIPi_RID4', 'WIPi_RID5', 'WIPi_RID6'],
        'transport_times': 1.0488        
    },
    'WIPo_ROD2': {
        'next': ['WIPi_RID1', 'WIPi_RID2', 'WIPi_RID3','WIPi_RID4', 'WIPi_RID5', 'WIPi_RID6'],
        'transport_times': 1.0488          
    },
    'WIPo_ROD3': {
        'next': ['WIPi_RID1', 'WIPi_RID2', 'WIPi_RID3','WIPi_RID4', 'WIPi_RID5', 'WIPi_RID6'],
        'transport_times': 1.0488    
    },
    'WIPo_ROD4': {
        'next': ['WIPi_RID1', 'WIPi_RID2', 'WIPi_RID3','WIPi_RID4', 'WIPi_RID5', 'WIPi_RID6'],
        'transport_times': 1.0488   
    },
    'WIPo_ROD5': {
        'next': ['WIPi_RID1', 'WIPi_RID2', 'WIPi_RID3','WIPi_RID4', 'WIPi_RID5', 'WIPi_RID6'],
        'transport_times': 1.0488
    },
    'WIPo_ROD6': {
        'next': ['WIPi_RID1', 'WIPi_RID2', 'WIPi_RID3','WIPi_RID4', 'WIPi_RID5', 'WIPi_RID6'],
        'transport_times': 1.0488          
    },
    'WIPo_ROD7': {
        'next': ['WIPi_RID1', 'WIPi_RID2', 'WIPi_RID3','WIPi_RID4', 'WIPi_RID5', 'WIPi_RID6'],
        'transport_times': 1.0488            
    },
    'WIPo_ROD8': {
        'next': ['WIPi_RID1', 'WIPi_RID2', 'WIPi_RID3','WIPi_RID4', 'WIPi_RID5', 'WIPi_RID6'],
        'transport_times': 1.0488  
    },
    'WIPo_ROD9': {
        'next': ['WIPi_RID1', 'WIPi_RID2', 'WIPi_RID3','WIPi_RID4', 'WIPi_RID5', 'WIPi_RID6'],
        'transport_times': 1.0488    
    },
    'WIPo_ROD10': {
        'next': ['WIPi_RID1', 'WIPi_RID2', 'WIPi_RID3','WIPi_RID4', 'WIPi_RID5', 'WIPi_RID6'],
        'transport_times': 1.0488
    },
    'WIPi_RID1': {
        'next': ['RID1'],
        'transport_times': 0
    },
    'WIPi_RID2': {
        'next': ['RID2'],
        'transport_times': 0        
    },
    'WIPi_RID3': {
        'next': ['RID3'],
        'transport_times': 0
    },
    'WIPi_RID4': {
        'next': ['RID4'],
        'transport_times': 0
    },
    'WIPi_RID5': {
        'next': ['RID5'],
        'transport_times': 0        
    },
    'WIPi_RID6': {
        'next': ['RID6'],
        'transport_times': 0
    },
    'RID1': {
        'process_time': 8.93,
        'OEE': 0.7251,
        'output': 'WIPo_RID1' 
    },
    'RID2': {
        'process_time': 8.93,
        'OEE': 0.7251,
        'output': 'WIPo_RID2'  
    },
    'RID3': {
        'process_time': 8.93,
        'OEE': 0.7251,
        'output': 'WIPo_RID3' 
    },
    'RID4': {
        'process_time': 8.93,
        'OEE': 0,
        'output': 'WIPo_RID4' 
    },
    'RID5': {
        'process_time': 8.93,
        'OEE': 0,
        'output': 'WIPo_RID5'  
    },
    'RID6': {
        'process_time': 8.93,
        'OEE': 0,
        'output': 'WIPo_RID6' 
    },
    'WIPo_RID1': {
        'next': ['WIPi_BR1', 'WIPi_BR2', 'WIPi_BR3', 'WIPi_BR4', 'WIPi_BR5', 'WIPi_BR6'],
        'transport_times': 1.1301        
    },
    'WIPo_RID2': {
        'next': ['WIPi_BR1', 'WIPi_BR2', 'WIPi_BR3', 'WIPi_BR4', 'WIPi_BR5', 'WIPi_BR6'],
        'transport_times': 1.1301         
    },
    'WIPo_RID3': {
        'next': ['WIPi_BR1', 'WIPi_BR2', 'WIPi_BR3', 'WIPi_BR4', 'WIPi_BR5', 'WIPi_BR6'],
        'transport_times': 1.1301 
    },
    'WIPo_RID4': {
        'next': ['WIPi_BR1', 'WIPi_BR2', 'WIPi_BR3', 'WIPi_BR4', 'WIPi_BR5', 'WIPi_BR6'],
        'transport_times': 1.1301        
    },
    'WIPo_RID5': {
        'next': ['WIPi_BR1', 'WIPi_BR2', 'WIPi_BR3', 'WIPi_BR4', 'WIPi_BR5', 'WIPi_BR6'],
        'transport_times': 1.1301         
    },
    'WIPo_RID6': {
        'next': ['WIPi_BR1', 'WIPi_BR2', 'WIPi_BR3', 'WIPi_BR4', 'WIPi_BR5', 'WIPi_BR6'],
        'transport_times': 1.1301 
    },
    'WIPi_BR1': {
        'next': ['BR1'],
        'transport_times': 0
    },
    'WIPi_BR2': {
        'next': ['BR2'],
        'transport_times': 0        
    },
    'WIPi_BR3': {
        'next': ['BR3'],
        'transport_times': 0        
    },
    'WIPi_BR4': {
        'next': ['BR4'],
        'transport_times': 0
    },
    'WIPi_BR5': {
        'next': ['BR5'],
        'transport_times': 0        
    },
    'WIPi_BR6': {
        'next': ['BR6'],
        'transport_times': 0        
    },
    'BR1': {
        'process_time': 8.8,
        'OEE': 0.8,
        'output': 'WIPo_BR1'         
    },
    'BR2': {
        'process_time': 8.8,
        'OEE': 0.8,
        'output': 'WIPo_BR2' 
    },
    'BR3': {
        'process_time': 8.8,
        'OEE': 0.8,
        'output': 'WIPo_BR3'        
    },
    'BR4': {
        'process_time': 8.8,
        'OEE': 0,
        'output': 'WIPo_BR4'         
    },
    'BR5': {
        'process_time': 8.8,
        'OEE': 0,
        'output': 'WIPo_BR5' 
    },
    'BR6': {
        'process_time': 8.8,
        'OEE': 0,
        'output': 'WIPo_BR6'        
    },
    'WIPo_BR1': {
        'next': ['finished_goods2'],
        'transport_times': 2
    },
    'WIPo_BR2': {
        'next': ['finished_goods2'],
        'transport_times': 2        
    },
    'WIPo_BR3': {
        'next': ['finished_goods2'],
        'transport_times': 2
    },
    'WIPo_BR4': {
        'next': ['finished_goods2'],
        'transport_times': 2
    },
    'WIPo_BR5': {
        'next': ['finished_goods2'],
        'transport_times': 2        
    },
    'WIPo_BR6': {
        'next': ['finished_goods2'],
        'transport_times': 2
    },
    'finished_goods2': {
        'next': ['WIPi_WC'],
        'transport_times': 4
    },
    'WIPi_WC': {
        'next': ['WC'],
        'transport_times': 0
    },
    'WC': {
        'process_time': 0.57,
        'OEE': 0.9,
        'output': 'WIPo_WC'  
    },
    'WIPo_WC': {
        'next': ['WIPi_GR'],
        'transport_times': 0
    },
    'WIPi_GR': {
        'next': ['GR'],
        'transport_times': 0.25
    },
    'GR': {
        'process_time': 31.5,
        'OEE': 0.9,
        'output': 'WIPo_GR'
    },
    'WIPo_GR': {
        'next': ['NIH1', 'NIH2'],
        'transport_times': 1
    },
    'NIH1': {
        'process_time': 1.75,
        'OEE': 0.77,
        'output': 'NP1'
    },
    'NIH2': {
        'process_time': 1.75,
        'OEE': 0.77, #0.77
        'output': 'NP2'
    },
    'NP1': {
        'process_time': 2.68,
        'OEE': 0.77,
        'output': 'WIPo_NP'
    },
    'NP2': {
        'process_time': 2.68,
        'OEE': 0.77,   #0.77
        'output': 'WIPo_NP'
    },
    'WIPo_NP': {
        'next': ['WIPi_RNB1', 'WIPi_RNB2','WIPi_RNB3','WIPi_RNB4'],
        'transport_times': [1, 1, 1, 1]
    },
    'WIPi_RNB1': {
        'next': ['RNB1'],
        'transport_times': 0
    },
    'RNB1': {
        'process_time': 8.95,                     #8.95
        'OEE': 0.899,                             #0.899
        'output': 'WIPo_RNB1'
    },
    'WIPo_RNB1': {
        'next': ['finished_goods3'],
        'transport_times': 1
    },
    'WIPi_RNB2': {
        'next': ['RNB2'],
        'transport_times': 0
    },
    'RNB2': {
        'process_time': 8.95,                     #8.95
        'OEE': 0.899,
        'output': 'WIPo_RNB2'
    },
    'WIPo_RNB2': {
        'next': ['finished_goods3'],
        'transport_times': 1
    },
    'WIPi_RNB3': {
        'next': ['RNB3'],
        'transport_times': 0
    },
    'RNB3': {
        'process_time': 8.95,                     #8.95
        'OEE': 0,
        'output': 'WIPo_RNB3'
    },
    'WIPo_RNB3': {
        'next': ['finished_goods3'],
        'transport_times': 1
    },
    'WIPi_RNB4': {
        'next': ['RNB4'],
        'transport_times': 0
    },
    'RNB4': {
        'process_time': 8.95,                     #8.95
        'OEE': 0,
        'output': 'WIPo_RNB4'
    },
    'WIPo_RNB4': {
        'next': ['finished_goods3'],
        'transport_times': 1
    },
    'finished_goods3': {
        'next': ['WIPi_PO1', 'WIPi_PO2', 'WIPi_PO3', 'WIPi_PO4', 'WIPi_PO5', 'WIPi_PO6'],
        'transport_times': [2.33, 2.33, 2.33, 2.33, 2.33, 2.33]
    },
    'WIPi_PO1': {
        'next': ['PO1'],
        'transport_times': 0
    },
    'WIPi_PO2': {
        'next': ['PO2'],
        'transport_times': 0
    },
    'WIPi_PO3': {
        'next': ['PO3'],
        'transport_times': 0
    },
    'WIPi_PO4': {
        'next': ['PO4'],
        'transport_times': 0
    },
    'WIPi_PO5': {
        'next': ['PO5'],
        'transport_times': 0
    },
    'WIPi_PO6': {
        'next': ['PO6'],
        'transport_times': 0
    },
    'PO1': {
        'process_time': 7.32,
        'OEE': 0.68,          #0.68
        'output': 'WIPo_PO1'
    },
    'PO2': {
        'process_time': 7.32,
        'OEE': 0.68,
        'output': 'WIPo_PO2'
    },
    'PO3': {
        'process_time': 7.32,
        'OEE': 0.68,
        'output': 'WIPo_PO3'
    },
    'PO4': {
        'process_time': 7.32,
        'OEE': 0,
        'output': 'WIPo_PO4'
    },
    'PO5': {
        'process_time': 7.32,
        'OEE': 0,
        'output': 'WIPo_PO5'
    },
    'PO6': {
        'process_time': 7.32,
        'OEE': 0,
        'output': 'WIPo_PO6'
    },
    'WIPo_PO1': {
        'next': ['WIPi_HT'],
        'transport_times': 2.59
    },
    'WIPo_PO2': {
        'next': ['WIPi_HT'],
        'transport_times': 2.27
    },    
    'WIPo_PO3': {
        'next': ['WIPi_HT'],
        'transport_times': 2.27
    },
    'WIPo_PO4': {
        'next': ['WIPi_HT'],
        'transport_times': 2.59
    },
    'WIPo_PO5': {
        'next': ['WIPi_HT'],
        'transport_times': 2.27
    },    
    'WIPo_PO6': {
        'next': ['WIPi_HT'],
        'transport_times': 2.27
    },
    'WIPi_HT': {
        'next': ['HT'],
        'transport_times': 0
    },
    'HT': {
        'process_time': 8.66,
        'OEE': 0.75,  #0.75
        'output': 'WIPo_HT',
        'capacity': 8                       
    },
    'WIPo_HT': {
        'next': ['WIPi_SPHDT'],
        'transport_times': [0.13]
    },
    'WIPi_SPHDT': {
        'next': ['SPHDT1','SPHDT2'],
        'transport_times': [0,0]
    },
    'SPHDT1': {
        'process_time': 1.42, #1.42
        'OEE': 0.96, #0.96 
        'output': 'WIPi_HDT1'
    },
    'SPHDT2': {
        'process_time': 1.42, #1.42
        'OEE': 0, #0.96 
        'output': 'WIPi_HDT2'
    },
    'WIPi_HDT1': {                 
        'next': ['HDT1'],
        'transport_times': 0,
#         'capacity': 1
    },
    'WIPi_HDT2': {                 
        'next': ['HDT2'],
        'transport_times': 0,
#         'capacity': 1
    },
    'HDT1': {
        'process_time': 2, #2
        'OEE': 0.96,
        'output': ['WIPo_HDT']
    },
    'HDT2': {
        'process_time': 2, #2
        'OEE': 0,
        'output': ['WIPo_HDT']
    },
    'WIPo_HDT': {
        'next': ['test_feed', 'hold'],
        'transport_times': 1.6504
    },
    'test_feed': {
        'next': ['WIPi_CUT'],
        'transport_times': 1
    },
    'scrap': {
        'next': [],
        'transport_times': 0
    },
    'WIPi_CUT': {
        'next': ['CUT1', 'CUT2', 'CUT3', 'CUT4'],
        'transport_times': [0, 0, 0, 0]
    },
    'CUT1': {
        'process_time': 13.77,
        'OEE': 0.8050,
        'output': 'WIPo_CUT'
    },
    'CUT2': {
        'process_time': 13.77,
        'OEE': 0.8050,
        'output': 'WIPo_CUT' 
    },
    'CUT3': {
        'process_time': 13.77,
        'OEE': 0.8050,
        'output': 'WIPo_CUT'         
    },
    'CUT4': {
        'process_time': 13.77,
        'OEE': 0.8050,
        'output': 'WIPo_CUT'         
    },
    'WIPo_CUT': {
        'next': ['WIPi_MTT1', 'WIPi_MTT2'],
        'transport_times': [1.59, 1.59]      
    },
    'WIPi_MTT1': {
        'next': ['MTT1'],
        'transport_times': 0
    },
    'MTT1': {
        'process_time': 13.77, #13.77
        'OEE': 0.85,
        'output': 'WIPo_MTT1'
    },
    'WIPo_MTT1': {
        'next': ['WIPi_TT1', 'WIPi_TT2'],
        'transport_times': [2.51, 2.51]
    },
    'WIPi_MTT2': {
        'next': ['MTT2'],
        'transport_times': 0
    },
    'MTT2': {
        'process_time': 13.77, #13.77
        'OEE': 0,
        'output': 'WIPo_MTT2'
    },
    'WIPo_MTT2': {
        'next': ['WIPi_TT1', 'WIPi_TT2'],
        'transport_times': [2.51, 2.51]
    },
    'WIPi_TT1': {
        'next': ['TT1'],
        'transport_times': 0
    },
    'TT1': {
        'process_time': 4.68,  #4.68
        'OEE': 0.85,
        'output': 'scrap'
    },
    'WIPi_TT2': {
        'next': ['TT2'],
        'transport_times': 0
    },
    'TT2': {
        'process_time': 4.68,  #4.68
        'OEE': 0,
        'output': 'scrap'
    },
    'hold': {
        'next': ['WIPi_HS'], 
        'transport_times': 2.43
    },
    'WIPi_HS': {
        'next': ['HS1', 'HS2'],
        'transport_times': [0,0]
    },
    'HS1': {
        'process_time': 0.6,
        'OEE': 0.85,
        'output': 'WIPo_HS'
    },
    'HS2': {
        'process_time': 0.6,
        'OEE': 0,
        'output': 'WIPo_HS'
    },
    'WIPo_HS': {
        'next': ['finished_goods4'],
        'transport_times': [2.19]
    },
    'finished_goods4': {
        'next': ['WIPi_FO1', 'WIPi_FO2', 'WIPi_FO3', 'WIPi_FO4','WIPi_FO5', 'WIPi_FO6', 'WIPi_FO7', 'WIPi_FO8'],
        'transport_times': [1.1667, 1.1667, 1.1667, 1.1667, 1.1667, 1.1667, 1.1667, 1.1667]
    },
    'WIPi_FO1': {
        'next': ['FO1'],
        'transport_times': 0 
    },
    'WIPi_FO2': {
        'next': ['FO2'],
        'transport_times': 0
    },
    'WIPi_FO3': {
        'next': ['FO3'],
        'transport_times': 0
    },
    'WIPi_FO4': {
        'next':['FO4'],
        'transport_times': 0
    },
    'WIPi_FO5': {
        'next': ['FO5'],
        'transport_times': 0 
    },
    'WIPi_FO6': {
        'next': ['FO6'],
        'transport_times': 0
    },
    'WIPi_FO7': {
        'next': ['FO7'],
        'transport_times': 0
    },
    'WIPi_FO8': {
        'next':['FO8'],
        'transport_times': 0
    },
    'FO1': {
        'process_time': 9.76,
        'OEE': 0.85,
        'output': 'WIPo_FO1'
    },
    'FO2': {
        'process_time': 9.76,
        'OEE': 0.85,
        'output': 'WIPo_FO2'
    },
    'FO3': {
        'process_time': 9.76,
        'OEE': 0.85,
        'output': 'WIPo_FO3'
    },
    'FO4': {
        'process_time': 9.76,
        'OEE': 0.85,
        'output': 'WIPo_FO4'
    },
    'FO5': {
        'process_time': 9.76,
        'OEE': 0,
        'output': 'WIPo_FO5'
    },
    'FO6': {
        'process_time': 9.76,
        'OEE': 0,
        'output': 'WIPo_FO6'
    },
    'FO7': {
        'process_time': 9.76,
        'OEE': 0,
        'output': 'WIPo_FO7'
    },
    'FO8': {
        'process_time': 9.76,
        'OEE': 0,
        'output': 'WIPo_FO8'
    },
    'WIPo_FO1': {
        'next': ['WIPi_UT'],
        'transport_times': 0.2155
    },
    'WIPo_FO2': {
        'next': ['WIPi_UT'],
        'transport_times': 0.2155
    },
    'WIPo_FO3': {
        'next': ['WIPi_UT'],
        'transport_times': 0.2155
    },
    'WIPo_FO4': {
        'next': ['WIPi_UT'],
        'transport_times': 0.2155
    },
    'WIPo_FO5': {
        'next': ['WIPi_UT'],
        'transport_times': 0.2155
    },
    'WIPo_FO6': {
        'next': ['WIPi_UT'],
        'transport_times': 0.2155
    },
    'WIPo_FO7': {
        'next': ['WIPi_UT'],
        'transport_times': 0.2155
    },
    'WIPo_FO8': {
        'next': ['WIPi_UT'],
        'transport_times': 0.2155
    },
    'WIPi_UT': {
        'next':['UT1','UT2'],
        'transport_times': [0,0]
    },
    'UT1': {
        'process_time': 1.44,
        'OEE': 0.85,
        'output': 'WIPo_UT'
    },
    'UT2': {
        'process_time': 1.44,
        'OEE': 0,
        'output': 'WIPo_UT'
    },
    'WIPo_UT': {
        'next': ['WIPi_SR'],
        'transport_times': 0.6504
    },
    'WIPi_SR': {
        'next':['SR1', 'SR2'],
        'transport_times': 0
    },
    'SR1': {
        'process_time': 1,
        'OEE': 0.85,
        'output': 'WIPo_SR'
    },  
    'SR2': {
        'process_time': 1,
        'OEE': 0.85,
        'output': 'WIPo_SR'
    }, 
    'WIPo_SR': {
        'next': ['WIPi_DB1', 'WIPi_DB2', 'WIPi_DB3', 'WIPi_DB4', 'WIPi_DB5', 'WIPi_DB6','WIPi_DB7', 'WIPi_DB8', 'WIPi_DB9', 'WIPi_DB10',                     'WIPi_DB11', 'WIPi_DB12'],
        'transport_times': 0.8943
    },
    'WIPi_DB1': {
        'next': ['DB1'],
        'transport_times': 0
    },
    'WIPi_DB2': {
        'next': ['DB2'],
        'transport_times': 0
    },
    'WIPi_DB3': {
        'next': ['DB3'],
        'transport_times': 0
    },
    'WIPi_DB4': {
        'next': ['DB4'],
        'transport_times': 0
    },
    'WIPi_DB5': {
        'next': ['DB5'],
        'transport_times': 0
    },
    'WIPi_DB6': {
        'next': ['DB6'],
        'transport_times': 0
    },
    'WIPi_DB7': {
        'next': ['DB7'],
        'transport_times': 0
    },
    'WIPi_DB8': {
        'next': ['DB8'],
        'transport_times': 0
    },
    'WIPi_DB9': {
        'next': ['DB9'],
        'transport_times': 0
    },
    'WIPi_DB10': {
        'next': ['DB10'],
        'transport_times': 0
    },
    'WIPi_DB11': {
        'next': ['DB11'],
        'transport_times': 0
    },
    'WIPi_DB12': {
        'next': ['DB12'],
        'transport_times': 0
    },
    'DB1': {
        'process_time': 15.18, 
        'OEE': 0.85,
        'next': 'WIPo_DB1'
    },
    'DB2': {
        'process_time': 15.18, 
        'OEE': 0.85,
        'next': 'WIPo_DB2'
    },
    'DB3': {
        'process_time': 15.18, 
        'OEE': 0.85,
        'next': 'WIPo_DB3'
    },
    'DB4': {
        'process_time': 15.18, 
        'OEE': 0.85,
        'next': 'WIPo_DB4'
    },
    'DB5': {
        'process_time': 15.18, 
        'OEE': 0.85,
        'next': 'WIPo_DB5'
    },
    'DB6': {
        'process_time': 15.18, 
        'OEE': 0.85,
        'next': 'WIPo_DB6'
    },
    'DB7': {
        'process_time': 15.18, 
        'OEE': 0,
        'next': 'WIPo_DB7'
    },
    'DB8': {
        'process_time': 15.18, 
        'OEE': 0,
        'next': 'WIPo_DB8'
    },
    'DB9': {
        'process_time': 15.18, 
        'OEE': 0,
        'next': 'WIPo_DB9'
    },
    'DB10': {
        'process_time': 15.18, 
        'OEE': 0,
        'next': 'WIPo_DB10'
    },
    'DB11': {
        'process_time': 15.18, 
        'OEE': 0,
        'next': 'WIPo_DB11'
    },
    'DB12': {
        'process_time': 15.18, 
        'OEE': 0,
        'next': 'WIPo_DB12'
    },
    'WIPo_DB1': {
        'next': ['WIPi_KN'],
        'transport_times': 0.6775
    },
    'WIPo_DB2': {
        'next': ['WIPi_KN'],
        'transport_times': 0.6775
    },
    'WIPo_DB3': {
        'next': ['WIPi_KN'],
        'transport_times': 0.6775
    },
    'WIPo_DB4': {
        'next': ['WIPi_KN'],
        'transport_times': 0.6775
    },
    'WIPo_DB5': {
        'next': ['WIPi_KN'],
        'transport_times': 0.6775
    },
    'WIPo_DB6': {
        'next': ['WIPi_KN'],
        'transport_times': 0.6775
    },
    'WIPo_DB7': {
        'next': ['WIPi_KN'],
        'transport_times': 0.6775
    },
    'WIPo_DB8': {
        'next': ['WIPi_KN'],
        'transport_times': 0.6775
    },
    'WIPo_DB9': {
        'next': ['WIPi_KN'],
        'transport_times': 0.6775
    },
    'WIPo_DB10': {
        'next': ['WIPi_KN'],
        'transport_times': 0.6775
    },
    'WIPo_DB11': {
        'next': ['WIPi_KN'],
        'transport_times': 0.6775
    },
    'WIPo_DB12': {
        'next': ['WIPi_KN'],
        'transport_times': 0.6775
    },
    'WIPi_KN': {
        'next': ['KN1', 'KN2', 'KN3', 'KN4'],
        'transport_times': 0
    },
    'KN1': {
        'process_time': 2.29,
        'OEE': 0.85,
        'next': ['WIPo_KN']
    },
    'KN2': {
        'process_time': 2.29,
        'OEE': 0.85,
        'next': ['WIPo_KN']
    },
    'KN3': {
        'process_time': 2.29,
        'OEE': 0,
        'next': ['WIPo_KN']
    },
    'KN4': {
        'process_time': 2.29,
        'OEE': 0,
        'next': ['WIPo_KN']
    },
    'WIPo_KN': {
        'next': ['WIPi_PDB1', 'WIPi_PDB2','WIPi_PDB3', 'WIPi_PDB4'],
        'transport_times': 0.4065
    },
    'WIPi_PDB1': {
        'next': ['PDB1'],
        'transport_times': 0
    },
    'PDB1': {
        'process_time': 4.92,
        'OEE': 0.85,
        'next': ['WIPo_PDB1'],
    },
    'WIPo_PDB1': {
        'next': ['WIPi_FC1', 'WIPi_FC2', 'WIPi_FC3', 'WIPi_FC4', 'WIPi_FC5', 'WIPi_FC6'],
        'transport_times': 0.5691
    },
    'WIPi_PDB2': {
        'next': ['PDB2'],
        'transport_times': 0
    },
    'PDB2': {
        'process_time': 4.92,
        'OEE': 0.85,
        'next': ['WIPo_PDB2'],
    },
    'WIPo_PDB2': {
        'next': ['WIPi_FC1', 'WIPi_FC2', 'WIPi_FC3', 'WIPi_FC4', 'WIPi_FC5', 'WIPi_FC6'],
        'transport_times': 0.5691
    },
    'WIPi_PDB3': {
        'next': ['PDB3'],
        'transport_times': 0
    },
    'PDB3': {
        'process_time': 4.92,
        'OEE': 0,
        'next': ['WIPo_PDB3'],
    },
    'WIPo_PDB3': {
        'next': ['WIPi_FC1', 'WIPi_FC2', 'WIPi_FC3', 'WIPi_FC4', 'WIPi_FC5', 'WIPi_FC6'],
        'transport_times': 0.5691
    },
    'WIPi_PDB4': {
        'next': ['PDB4'],
        'transport_times': 0
    },
    'PDB4': {
        'process_time': 4.92,
        'OEE': 0,
        'next': ['WIPo_PDB4'],
    },
    'WIPo_PDB4': {
        'next': ['WIPi_FC1', 'WIPi_FC2', 'WIPi_FC3', 'WIPi_FC4', 'WIPi_FC5', 'WIPi_FC6'],
        'transport_times': 0.5691
    },
    'WIPi_FC1': {
        'next': ['FC1'],
        'transport_times': 0
    },
    'WIPi_FC2': {
        'next': ['FC2'],
        'transport_times': 0
    },
    'WIPi_FC3': {
        'next': ['FC3'],
        'transport_times': 0
    },
    'WIPi_FC4': {
        'next': ['FC4'],
        'transport_times': 0
    },
    'WIPi_FC5': {
        'next': ['FC5'],
        'transport_times': 0
    },
    'WIPi_FC6': {
        'next': ['FC6'],
        'transport_times': 0
    },
    'FC1': {
        'process_time': 10.76,
        'OEE': 0.85,
        'next': ['WIPo_FC1']
    },
    'FC2': {
        'process_time': 10.76,
        'OEE': 0.85,
        'next': ['WIPo_FC2']
    },
    'FC3': {
        'process_time': 10.76,
        'OEE': 0,
        'next': ['WIPo_FC3']
    },
    'FC4': {
        'process_time': 10.76,
        'OEE': 0,
        'next': ['WIPo_FC4']
    },
    'FC5': {
        'process_time': 10.76,
        'OEE': 0,
        'next': ['WIPo_FC5']
    },
    'FC6': {
        'process_time': 10.76,
        'OEE': 0,
        'next': ['WIPo_FC6']
    },
    'WIPo_FC1': {
        'next': ['WIPi_SP1', 'WIPi_SP2'],
        'transport_times': 0.5691
    },
    'WIPo_FC2': {
        'next': ['WIPi_SP1', 'WIPi_SP2'],
        'transport_times': 0.5691
    },
    'WIPo_FC3': {
        'next': ['WIPi_SP1', 'WIPi_SP2'],
        'transport_times': 0.5691
    },
    'WIPo_FC4': {
        'next': ['WIPi_SP1', 'WIPi_SP2'],
        'transport_times': 0.5691
    },
    'WIPo_FC5': {
        'next': ['WIPi_SP1', 'WIPi_SP2'],
        'transport_times': 0.5691
    },
    'WIPo_FC6': {
        'next': ['WIPi_SP1', 'WIPi_SP2'],
        'transport_times': 0.5691
    },
    'WIPi_SP1': {
        'next': ['SP1'],
        'transport_times': 0
    },
    'SP1': {
        'process_time': 2.5667,
        'OEE': 0.85,
        'next': ['WIPo_SP1']
    },
    'WIPo_SP1': {
        'next': ['finished_goods5'],
        'transport_times': 1.3740
    },
    'WIPi_SP2': {
        'next': ['SP2'],
        'transport_times': 0
    },
    'SP2': {
        'process_time': 2.5667,
        'OEE': 0,
        'next': ['WIPo_SP2']
    },
    'WIPo_SP2': {
        'next': ['finished_goods5'],
        'transport_times': 1.3740
    },
    'finished_goods5': {
        'next': ['WIPi_RG'],
        'transport_times': 0
    },
    'WIPi_RG': {
        'next': ['RG1', 'RG2', 'RG3', 'RG4', 'RG5', 'RG6','RG7', 'RG8', 'RG9', 'RG10', 'RG11', 'RG12'],
        'transport_times': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    },
    'RG1': {
        'process_time': 11.76,
        'OEE': 0.97,
        'next': ['WIPo_RG']
    },
    'RG2': {
        'process_time': 11.76,
        'OEE': 0.97,
        'next': ['WIPo_RG']
    },
    'RG3': {
        'process_time': 11.76,
        'OEE': 0.97,
        'next': ['WIPo_RG']
    },
    'RG4': {
        'process_time': 11.76,
        'OEE': 0.97,
        'next': ['WIPo_RG']
    },
    'RG5': {
        'process_time': 11.76,
        'OEE': 0.97,
        'next': ['WIPo_RG']
    },
    'RG6': {
        'process_time': 11.76,
        'OEE': 0.97,
        'next': ['WIPo_RG']
    },
    'RG7': {
        'process_time': 11.76,
        'OEE': 0,
        'next': ['WIPo_RG']
    },
    'RG8': {
        'process_time': 11.76,
        'OEE': 0,
        'next': ['WIPo_RG']
    },
    'RG9': {
        'process_time': 11.76,
        'OEE': 0,
        'next': ['WIPo_RG']
    },
    'RG10': {
        'process_time': 11.76,
        'OEE': 0,
        'next': ['WIPo_RG']
    },
    'RG11': {
        'process_time': 11.76,
        'OEE': 0,
        'next': ['WIPo_RG']
    },
    'RG12': {
        'process_time': 11.76,
        'OEE': 0,
        'next': ['WIPo_RG']
    },
    'WIPo_RG': {
        'next': ['WIPi_SB1', 'WIPi_SB2', 'WIPi_SB3', 'WIPi_SB4', 'WIPi_SB5', 'WIPi_SB6', 'WIPi_SB7', 'WIPi_SB8', 'WIPi_SB9', 'WIPi_SB10'],
        'transport_times': [1.3833, 1.3833, 1.3833, 1.3833, 1.3833, 1.3833, 1.3833, 1.3833, 1.3833, 1.3833]
    },
    'WIPi_SB1': {
        'next': ['SB1'],
        'transport_times': 0
    },
    'WIPi_SB2': {
        'next': ['SB2'],
        'transport_times': 0
    },
    'WIPi_SB3': {
        'next': ['SB3'],
        'transport_times': 0
    },
    'WIPi_SB4': {
        'next': ['SB4'],
        'transport_times': 0
    },
    'WIPi_SB5': {
        'next': ['SB5'],
        'transport_times': 0
    },
    'WIPi_SB6': {
        'next': ['SB6'],
        'transport_times': 0
    },
    'WIPi_SB7': {
        'next': ['SB7'],
        'transport_times': 0
    },
    'WIPi_SB8': {
        'next': ['SB8'],
        'transport_times': 0
    },
    'WIPi_SB9': {
        'next': ['SB9'],
        'transport_times': 0
    },
    'WIPi_SB10': {
        'next': ['SB10'],
        'transport_times': 0
    },
    'SB1': {
        'process_time': 2.35,
        'OEE': 0.97,
        'next': ['WIPo_SB1']
    },
    'SB2': {
        'process_time': 2.35,
        'OEE': 0.97,
        'next': ['WIPo_SB2']
    },
    'SB3': {
        'process_time': 2.35,
        'OEE': 0.97,
        'next': ['WIPo_SB3']
    },
    'SB4': {
        'process_time': 2.35,
        'OEE': 0.97,
        'next': ['WIPo_SB4']
    },
    'SB5': {
        'process_time': 2.35,
        'OEE': 0.97,
        'next': ['WIPo_SB5']
    },
    'SB6': {
        'process_time': 2.35,
        'OEE': 0,
        'next': ['WIPo_SB6']
    },
    'SB7': {
        'process_time': 2.35,
        'OEE': 0,
        'next': ['WIPo_SB7']
    },
    'SB8': {
        'process_time': 2.35,
        'OEE': 0,
        'next': ['WIPo_SB8']
    },
    'SB9': {
        'process_time': 2.35,
        'OEE': 0,
        'next': ['WIPo_SB9']
    },
    'SB10': {
        'process_time': 2.35,
        'OEE': 0,
        'next': ['WIPo_SB10']
    },
    'WIPo_SB1': {
        'next': ['WIPi_NT1', 'WIPi_NT2', 'WIPi_NT3', 'WIPi_NT4', 'WIPi_NT5', 'WIPi_NT6'],
        'transport_times': [1.8130, 1.8130, 1.8130, 1.8130, 1.8130, 1.8130]
    },
    'WIPo_SB2': {
        'next': ['WIPi_NT1', 'WIPi_NT2', 'WIPi_NT3', 'WIPi_NT4', 'WIPi_NT5', 'WIPi_NT6'],
        'transport_times': [1.8130, 1.8130, 1.8130, 1.8130, 1.8130, 1.8130]
    },
    'WIPo_SB3': {
        'next': ['WIPi_NT1', 'WIPi_NT2', 'WIPi_NT3', 'WIPi_NT4', 'WIPi_NT5', 'WIPi_NT6'],
        'transport_times': [1.8130, 1.8130, 1.8130, 1.8130, 1.8130, 1.8130]
    },
    'WIPo_SB4': {
        'next': ['WIPi_NT1', 'WIPi_NT2', 'WIPi_NT3', 'WIPi_NT4', 'WIPi_NT5', 'WIPi_NT6'],
        'transport_times': [1.8130, 1.8130, 1.8130, 1.8130, 1.8130, 1.8130]
    },
    'WIPo_SB5': {
        'next': ['WIPi_NT1', 'WIPi_NT2', 'WIPi_NT3', 'WIPi_NT4', 'WIPi_NT5', 'WIPi_NT6'],
        'transport_times': [1.8130, 1.8130, 1.8130, 1.8130, 1.8130, 1.8130]
    },
    'WIPo_SB6': {
        'next': ['WIPi_NT1', 'WIPi_NT2', 'WIPi_NT3', 'WIPi_NT4', 'WIPi_NT5', 'WIPi_NT6'],
        'transport_times': [1.8130, 1.8130, 1.8130, 1.8130, 1.8130, 1.8130]
    },
    'WIPo_SB7': {
        'next': ['WIPi_NT1', 'WIPi_NT2', 'WIPi_NT3', 'WIPi_NT4', 'WIPi_NT5', 'WIPi_NT6'],
        'transport_times': [1.8130, 1.8130, 1.8130, 1.8130, 1.8130, 1.8130]
    },
    'WIPo_SB8': {
        'next': ['WIPi_NT1', 'WIPi_NT2', 'WIPi_NT3', 'WIPi_NT4', 'WIPi_NT5', 'WIPi_NT6'],
        'transport_times': [1.8130, 1.8130, 1.8130, 1.8130, 1.8130, 1.8130]
    },
    'WIPo_SB9': {
        'next': ['WIPi_NT1', 'WIPi_NT2', 'WIPi_NT3', 'WIPi_NT4', 'WIPi_NT5', 'WIPi_NT6'],
        'transport_times': [1.8130, 1.8130, 1.8130, 1.8130, 1.8130, 1.8130]
    },
    'WIPo_SB10': {
        'next': ['WIPi_NT1', 'WIPi_NT2', 'WIPi_NT3', 'WIPi_NT4', 'WIPi_NT5', 'WIPi_NT6'],
        'transport_times': [1.8130, 1.8130, 1.8130, 1.8130, 1.8130, 1.8130]
    },
#     'WIPo_RG': {
#         'next': ['WIPi_SB1', 'WIPi_SB2', 'WIPi_SB3', 'WIPi_SB4', 'WIPi_SB5', 'WIPi_SB6', 'WIPi_SB7', 'WIPi_SB8', 'WIPi_SB9', 'WIPi_SB10'],
#         'transport_times': [1.3833, 1.3833, 1.3833, 1.3833, 1.3833, 1.3833, 1.3833, 1.3833, 1.3833, 1.3833]
#     },
#     'WIPi_SB1': {
#         'next': ['SB1'],
#         'transport_times': 0
#     },
#     'WIPi_SB2': {
#         'next': ['SB2'],
#         'transport_times': 0
#     },
#     'WIPi_SB3': {
#         'next': ['SB3'],
#         'transport_times': 0
#     },
#     'WIPi_SB4': {
#         'next': ['SB4'],
#         'transport_times': 0
#     },
#     'WIPi_SB5': {
#         'next': ['SB5'],
#         'transport_times': 0
#     },
#     'WIPi_SB6': {
#         'next': ['SB6'],
#         'transport_times': 0
#     },
#     'WIPi_SB7': {
#         'next': ['SB7'],
#         'transport_times': 0
#     },
#     'WIPi_SB8': {
#         'next': ['SB8'],
#         'transport_times': 0
#     },
#     'WIPi_SB9': {
#         'next': ['SB9'],
#         'transport_times': 0
#     },
#     'WIPi_SB10': {
#         'next': ['SB10'],
#         'transport_times': 0
#     },
#     'SB1': {
#         'process_time': 2.35,
#         'OEE': 0.97,
#         'next': ['WIPo_SB1']
#     },
#     'SB2': {
#         'process_time': 2.35,
#         'OEE': 0.97,
#         'next': ['WIPo_SB2']
#     },
#     'SB3': {
#         'process_time': 2.35,
#         'OEE': 0.97,
#         'next': ['WIPo_SB3']
#     },
#     'SB4': {
#         'process_time': 2.35,
#         'OEE': 0.97,
#         'next': ['WIPo_SB4']
#     },
#     'SB5': {
#         'process_time': 2.35,
#         'OEE': 0.97,
#         'next': ['WIPo_SB5']
#     },
#     'SB6': {
#         'process_time': 2.35,
#         'OEE': 0,
#         'next': ['WIPo_SB6']
#     },
#     'SB7': {
#         'process_time': 2.35,
#         'OEE': 0,
#         'next': ['WIPo_SB7']
#     },
#     'SB8': {
#         'process_time': 2.35,
#         'OEE': 0,
#         'next': ['WIPo_SB8']
#     },
#     'SB9': {
#         'process_time': 2.35,
#         'OEE': 0,
#         'next': ['WIPo_SB9']
#     },
#     'SB10': {
#         'process_time': 2.35,
#         'OEE': 0,
#         'next': ['WIPo_SB10']
#     },
#     'WIPo_SB1': {
#         'next': ['WIPi_NT1', 'WIPi_NT2', 'WIPi_NT3', 'WIPi_NT4', 'WIPi_NT5', 'WIPi_NT6'],
#         'transport_times': [1.8130, 1.8130, 1.8130, 1.8130, 1.8130, 1.8130]
#     },
#     'WIPo_SB2': {
#         'next': ['WIPi_NT1', 'WIPi_NT2', 'WIPi_NT3', 'WIPi_NT4', 'WIPi_NT5', 'WIPi_NT6'],
#         'transport_times': [1.8130, 1.8130, 1.8130, 1.8130, 1.8130, 1.8130]
#     },
#     'WIPo_SB3': {
#         'next': ['WIPi_NT1', 'WIPi_NT2', 'WIPi_NT3', 'WIPi_NT4', 'WIPi_NT5', 'WIPi_NT6'],
#         'transport_times': [1.8130, 1.8130, 1.8130, 1.8130, 1.8130, 1.8130]
#     },
#     'WIPo_SB4': {
#         'next': ['WIPi_NT1', 'WIPi_NT2', 'WIPi_NT3', 'WIPi_NT4', 'WIPi_NT5', 'WIPi_NT6'],
#         'transport_times': [1.8130, 1.8130, 1.8130, 1.8130, 1.8130, 1.8130]
#     },
#     'WIPo_SB5': {
#         'next': ['WIPi_NT1', 'WIPi_NT2', 'WIPi_NT3', 'WIPi_NT4', 'WIPi_NT5', 'WIPi_NT6'],
#         'transport_times': [1.8130, 1.8130, 1.8130, 1.8130, 1.8130, 1.8130]
#     },
#     'WIPo_SB6': {
#         'next': ['WIPi_NT1', 'WIPi_NT2', 'WIPi_NT3', 'WIPi_NT4', 'WIPi_NT5', 'WIPi_NT6'],
#         'transport_times': [1.8130, 1.8130, 1.8130, 1.8130, 1.8130, 1.8130]
#     },
#     'WIPo_SB7': {
#         'next': ['WIPi_NT1', 'WIPi_NT2', 'WIPi_NT3', 'WIPi_NT4', 'WIPi_NT5', 'WIPi_NT6'],
#         'transport_times': [1.8130, 1.8130, 1.8130, 1.8130, 1.8130, 1.8130]
#     },
#     'WIPo_SB8': {
#         'next': ['WIPi_NT1', 'WIPi_NT2', 'WIPi_NT3', 'WIPi_NT4', 'WIPi_NT5', 'WIPi_NT6'],
#         'transport_times': [1.8130, 1.8130, 1.8130, 1.8130, 1.8130, 1.8130]
#     },
#     'WIPo_SB9': {
#         'next': ['WIPi_NT1', 'WIPi_NT2', 'WIPi_NT3', 'WIPi_NT4', 'WIPi_NT5', 'WIPi_NT6'],
#         'transport_times': [1.8130, 1.8130, 1.8130, 1.8130, 1.8130, 1.8130]
#     },
#     'WIPo_SB10': {
#         'next': ['WIPi_NT1', 'WIPi_NT2', 'WIPi_NT3', 'WIPi_NT4', 'WIPi_NT5', 'WIPi_NT6'],
#         'transport_times': [1.8130, 1.8130, 1.8130, 1.8130, 1.8130, 1.8130]
#     },
    'WIPi_NT1': {
        'next': ['NT1'],
        'transport_times': 0
    },
    'WIPi_NT2': {
        'next': ['NT2'],
        'transport_times': 0
    },
    'WIPi_NT3': {
        'next': ['NT3'],
        'transport_times': 0
    },
    'WIPi_NT4': {
        'next': ['NT4'],
        'transport_times': 0
    },
    'WIPi_NT5': {
        'next': ['NT5'],
        'transport_times': 0
    },
    'WIPi_NT6': {
        'next': ['NT6'],
        'transport_times': 0
    },
    'NT1': {
        'process_time': 10.53,
        'OEE': 0.924,
        'next': ['WIPo_NT1']
    },
    'NT2': {
        'process_time': 10.53,
        'OEE': 0.924,
        'next': ['WIPo_NT2']
    },
    'NT3': {
        'process_time': 10.53,
        'OEE': 0.924,
        'next': ['WIPo_NT3']
    },
    'NT4': {
        'process_time': 10.53,
        'OEE': 0,
        'next': ['WIPo_NT4']
    },
    'NT5': {
        'process_time': 10.53,
        'OEE': 0,
        'next': ['WIPo_NT5']
    },
    'NT6': {
        'process_time': 10.53,
        'OEE': 0,
        'next': ['WIPo_NT6']
    },
    'WIPo_NT1': {
        'next': ['WIPi_BT1', 'WIPi_BT2', 'WIPi_BT3', 'WIPi_BT4', 'WIPi_BT5', 'WIPi_BT6'],
        'transport_times': [2.1545, 2.1545, 2.1545, 2.1545, 2.1545, 2.1545]
    },
    'WIPo_NT2': {
        'next': ['WIPi_BT1', 'WIPi_BT2', 'WIPi_BT3', 'WIPi_BT4', 'WIPi_BT5', 'WIPi_BT6'],
        'transport_times': [2.1545, 2.1545, 2.1545, 2.1545, 2.1545, 2.1545]
    },
    'WIPo_NT3': {
        'next': ['WIPi_BT1', 'WIPi_BT2', 'WIPi_BT3', 'WIPi_BT4', 'WIPi_BT5', 'WIPi_BT6'],
        'transport_times': [2.1545, 2.1545, 2.1545, 2.1545, 2.1545, 2.1545]
    },
    'WIPo_NT4': {
        'next': ['WIPi_BT1', 'WIPi_BT2', 'WIPi_BT3', 'WIPi_BT4', 'WIPi_BT5', 'WIPi_BT6'],
        'transport_times': [2.1545, 2.1545, 2.1545, 2.1545, 2.1545, 2.1545]
    },
    'WIPo_NT5': {
        'next': ['WIPi_BT1', 'WIPi_BT2', 'WIPi_BT3', 'WIPi_BT4', 'WIPi_BT5', 'WIPi_BT6'],
        'transport_times': [2.1545, 2.1545, 2.1545, 2.1545, 2.1545, 2.1545]
    },
    'WIPo_NT6': {
        'next': ['WIPi_BT1', 'WIPi_BT2', 'WIPi_BT3', 'WIPi_BT4', 'WIPi_BT5', 'WIPi_BT6'],
        'transport_times': [2.1545, 2.1545, 2.1545, 2.1545, 2.1545, 2.1545]
    },
    'WIPi_BT1': {
        'next': ['BT1'],
        'transport_times': 0
    },
    'WIPi_BT2': {
        'next': ['BT2'],
        'transport_times': 0
    },
    'WIPi_BT3': {
        'next': ['BT3'],
        'transport_times': 0
    },
    'WIPi_BT4': {
        'next': ['BT4'],
        'transport_times': 0
    },
    'WIPi_BT5': {
        'next': ['BT5'],
        'transport_times': 0
    },
    'WIPi_BT6': {
        'next': ['BT6'],
        'transport_times': 0
    },
    'BT1': {
        'process_time': 9.38,
        'OEE': 0.924,
        'next': ['WIPo_BT1']
    },
    'BT2': {
        'process_time': 9.38,
        'OEE': 0.924,
        'next': ['WIPo_BT2']
    },
    'BT3': {
        'process_time': 9.38,
        'OEE': 0.924,
        'next': ['WIPo_BT3']
    },
    'BT4': {
        'process_time': 9.38,
        'OEE': 0,
        'next': ['WIPo_BT4']
    },
    'BT5': {
        'process_time': 9.38,
        'OEE': 0,
        'next': ['WIPo_BT5']
    },
    'BT6': {
        'process_time': 9.38,
        'OEE': 0,
        'next': ['WIPo_BT6']
    },
    'WIPo_BT1': {
        'next': ['WIPi_MP1', 'WIPi_MP2', 'WIPi_MP3', 'WIPi_MP4'],
        'transport_times': [2.5610, 2.5610, 2.5610, 2.5610]
    },
    'WIPo_BT2': {
        'next': ['WIPi_MP1', 'WIPi_MP2', 'WIPi_MP3', 'WIPi_MP4'],
        'transport_times': [2.5610, 2.5610, 2.5610, 2.5610]
    },
    'WIPo_BT3': {
        'next': ['WIPi_MP1', 'WIPi_MP2', 'WIPi_MP3', 'WIPi_MP4'],
        'transport_times': [2.5610, 2.5610, 2.5610, 2.5610]
    },
    'WIPo_BT4': {
        'next': ['WIPi_MP1', 'WIPi_MP2', 'WIPi_MP3', 'WIPi_MP4'],
        'transport_times': [2.5610, 2.5610, 2.5610, 2.5610]
    },
    'WIPo_BT5': {
        'next': ['WIPi_MP1', 'WIPi_MP2', 'WIPi_MP3', 'WIPi_MP4'],
        'transport_times': [2.5610, 2.5610, 2.5610, 2.5610]
    },
    'WIPo_BT6': {
        'next': ['WIPi_MP1', 'WIPi_MP2', 'WIPi_MP3', 'WIPi_MP4'],
        'transport_times': [2.5610, 2.5610, 2.5610, 2.5610]
    },
    'WIPi_MP1': {
        'next': ['MP1'],
        'transport_times': 0
    },
    'WIPi_MP2': {
        'next': ['MP2'],
        'transport_times': 0
    },
    'WIPi_MP3': {
        'next': ['MP3'],
        'transport_times': 0
    },
    'WIPi_MP4': {
        'next': ['MP4'],
        'transport_times': 0
    },
    'MP1': {
        'process_time': 3.51,
        'OEE': 1,
        'next': ['WIPo_MP1']
    },
    'MP2': {
        'process_time': 3.51,
        'OEE': 1,
        'next': ['WIPo_MP2']
    },
    'MP3': {
        'process_time': 3.51,
        'OEE': 0,
        'next': ['WIPo_MP3']
    },
    'MP4': {
        'process_time': 3.51,
        'OEE': 0,
        'next': ['WIPo_MP4']
    },
    'WIPo_MP1': {
        'next': ['WIPi_FB'],
        'transport_times': 1.4228
    },
    'WIPo_MP2': {
        'next': ['WIPi_FB'],
        'transport_times': 1.4228
    },
    'WIPo_MP3': {
        'next': ['WIPi_FB'],
        'transport_times': 1.4228
    },
    'WIPo_MP4': {
        'next': ['WIPi_FB'],
        'transport_times': 1.4228
    },
    'WIPi_FB': {
        'next': ['FB1', 'FB2', 'FB3', 'FB4'],
        'trasnport_times': [0, 0, 0, 0]
    },
    'FB1': {
        'process_time': 5.5,
        'OEE': 1,
        'next': ['WIPo_FB1']
    },
    'FB2': {
        'process_time': 5.5,
        'OEE': 1,
        'next': ['WIPo_FB2']
    },
    'FB3': {
        'process_time': 5.5,
        'OEE': 0,
        'next': ['WIPo_FB3']
    },
    'FB4': {
        'process_time': 5.5,
        'OEE': 0,
        'next': ['WIPo_FB4']
    },
    'WIPo_FB1': {
        'next': ['WIPi_FI'],
        'transport_times': 0
    },
    'WIPo_FB2': {
        'next': ['WIPi_FI'],
        'transport_times': 0
    },
    'WIPo_FB3': {
        'next': ['WIPi_FI'],
        'transport_times': 0
    },
    'WIPo_FB4': {
        'next': ['WIPi_FI'],
        'transport_times': 0
    },
    'WIPi_FI': {
        'next': ['FI1', 'FI2', 'FI3', 'FI4'],
        'transport_times': [0,0,0,0]
    },
    'FI1': {
        'process_time': 4.65,
        'OEE': 1,
        'next': ['WIPo_FI1']
    },
    'FI2': {
        'process_time': 4.65,
        'OEE': 1,
        'next': ['WIPo_FI2']
    },
    'FI3': {
        'process_time': 4.65,
        'OEE': 0,
        'next': ['WIPo_FI3']
    },
    'FI4': {
        'process_time': 4.65,
        'OEE': 0,
        'next': ['WIPo_FI4']
    },
    'WIPo_FI1': {
        'next': ['WIPi_D&P1', 'WIPi_D&P2', 'WIPi_D&P3', 'WIPi_D&P4'],
        'transport_times': [1.2927, 1.2927, 1.2927, 1.2927]
    },
    'WIPo_FI2': {
        'next': ['WIPi_D&P1', 'WIPi_D&P2', 'WIPi_D&P3', 'WIPi_D&P4'],
        'transport_times': [1.2927, 1.2927, 1.2927, 1.2927]
    },
    'WIPo_FI3': {
        'next': ['WIPi_D&P1', 'WIPi_D&P2', 'WIPi_D&P3', 'WIPi_D&P4'],
        'transport_times': [1.2927, 1.2927, 1.2927, 1.2927]
    },
    'WIPo_FI4': {
        'next': ['WIPi_D&P1', 'WIPi_D&P2', 'WIPi_D&P3', 'WIPi_D&P4'],
        'transport_times': [1.2927, 1.2927, 1.2927, 1.2927]
    },
    'WIPi_D&P1': {
        'next': ['D&P1'],
        'transport_times': 0
    },
    'WIPi_D&P2': {
        'next': ['D&P2'],
        'transport_times': 0
    },
    'WIPi_D&P3': {
        'next': ['D&P3'],
        'transport_times': 0
    },
    'WIPi_D&P4': {
        'next': ['D&P4'],
        'transport_times': 0
    },
    'D&P1': {
        'process_time': 15,  #4.69
        'OEE': 1,
        'next': ['WIPo_D&P1']
    },
    'D&P2': {
        'process_time': 15,  #4.69
        'OEE': 1,
        'next': ['WIPo_D&P2']
    },
    'D&P3': {
        'process_time': 15,  #4.69
        'OEE': 0,
        'next': ['WIPo_D&P3']
    },
    'D&P4': {
        'process_time': 15,  #4.69
        'OEE': 0,
        'next': ['WIPo_D&P4']
    },
    'WIPo_D&P1': {
        'next': ['finished_goods6'],
        'transport_times': 1.5
    },
    'WIPo_D&P2': {
        'next': ['finished_goods6'],
        'transport_times': 1.5
    },
    'WIPo_D&P3': {
        'next': ['finished_goods6'],
        'transport_times': 1.5
    },
    'WIPo_D&P4': {
        'next': ['finished_goods6'],
        'transport_times': 1.5
    },
}

MACHINE_INPUT = {
    'SB1':  'WIPi_SB1',
    'ROD1': 'WIPi_ROD',
    'ROD2': 'WIPi_ROD',
    'ROD3': 'WIPi_ROD',
    'ROD4': 'WIPi_ROD',
    'ROD5': 'WIPi_ROD',
    'ROD6': 'WIPi_ROD',
    'ROD7': 'WIPi_ROD',
    'ROD8': 'WIPi_ROD',
    'ROD9': 'WIPi_ROD',
    'ROD10': 'WIPi_ROD',
    'RID1': 'WIPi_RID1',
    'RID2': 'WIPi_RID2',    
    'RID3': 'WIPi_RID3',
    'RID4': 'WIPi_RID4',
    'RID5': 'WIPi_RID5',    
    'RID6': 'WIPi_RID6',
    'BR1': 'WIPi_BR1',
    'BR2': 'WIPi_BR2',    
    'BR3': 'WIPi_BR3',
    'BR4': 'WIPi_BR4',
    'BR5': 'WIPi_BR5',    
    'BR6': 'WIPi_BR6',
    'WC': 'WIPi_WC', 
    'GR': 'GR',
    'NIH1': 'NIH1',
    'NIH2': 'NIH2',
    'NP1': 'NP1',
    'NP2': 'NP2', 
    'RNB1': 'WIPi_RNB1',
    'RNB2': 'WIPi_RNB2',
    'RNB3': 'WIPi_RNB3',
    'RNB4': 'WIPi_RNB4',
    'PO1': 'WIPi_PO1',
    'PO2': 'WIPi_PO2',
    'PO3': 'WIPi_PO3', 
    'PO4': 'WIPi_PO4',
    'PO5': 'WIPi_PO5',
    'PO6': 'WIPi_PO6', 
    'HT': 'WIPi_HT',
    'SPHDT1': 'WIPi_SPHDT',
    'SPHDT2': 'WIPi_SPHDT',
    'HDT1': 'WIPi_HDT1',
    'HDT2': 'WIPi_HDT2',
    'CUT1': 'WIPi_CUT',
    'CUT2': 'WIPi_CUT',
    'CUT3': 'WIPi_CUT',
    'CUT4': 'WIPi_CUT',
    'MTT1': 'WIPi_MTT1',
    'MTT2': 'WIPi_MTT2',
    'TT1': 'WIPi_TT1',
    'TT2': 'WIPi_TT2',
    'HS1': 'WIPi_HS',
    'HS2': 'WIPi_HS',
    'FO1': 'WIPi_FO1',
    'FO2': 'WIPi_FO2',
    'FO3': 'WIPi_FO3',
    'FO4': 'WIPi_FO4',
    'FO5': 'WIPi_FO5',
    'FO6': 'WIPi_FO6',
    'FO7': 'WIPi_FO7',
    'FO8': 'WIPi_FO8',
    'UT1': 'WIPi_UT', 
    'UT2': 'WIPi_UT',
    'SR1': 'WIPi_SR',
    'SR2': 'WIPi_SR',
    'DB1': 'WIPi_DB1',
    'DB2': 'WIPi_DB2',
    'DB3': 'WIPi_DB3',
    'DB4': 'WIPi_DB4',
    'DB5': 'WIPi_DB5',
    'DB6': 'WIPi_DB6',
    'DB7': 'WIPi_DB7',
    'DB8': 'WIPi_DB8',
    'DB9': 'WIPi_DB9',
    'DB10': 'WIPi_DB10',
    'DB11': 'WIPi_DB11',
    'DB12': 'WIPi_DB12',
    'KN1': 'WIPi_KN',
    'KN2': 'WIPi_KN',
    'KN3': 'WIPi_KN',
    'KN4': 'WIPi_KN',
    'PDB1': 'WIPi_PDB1',
    'PDB2': 'WIPi_PDB2',
    'PDB3': 'WIPi_PDB3',
    'PDB4': 'WIPi_PDB4',
    'FC1': 'WIPi_FC1', 
    'FC2': 'WIPi_FC2', 
    'FC3': 'WIPi_FC3',
    'FC4': 'WIPi_FC4', 
    'FC5': 'WIPi_FC5', 
    'FC6': 'WIPi_FC6',
    'SP1': 'WIPi_SP1',
    'SP2': 'WIPi_SP2',
        # RG block (shared pallet)
    'RG1': 'WIPi_RG',
    'RG2': 'WIPi_RG',
    'RG3': 'WIPi_RG',
    'RG4': 'WIPi_RG',
    'RG5': 'WIPi_RG',
    'RG6': 'WIPi_RG',
    'RG7': 'WIPi_RG',
    'RG8': 'WIPi_RG',
    'RG9': 'WIPi_RG',
    'RG10': 'WIPi_RG',
    'RG11': 'WIPi_RG',
    'RG12': 'WIPi_RG',
    # SB block
    'SB1': 'WIPi_SB1',
    'SB2': 'WIPi_SB2',
    'SB3': 'WIPi_SB3',
    'SB4': 'WIPi_SB4',
    'SB5': 'WIPi_SB5',
    'SB6': 'WIPi_SB6',
    'SB7': 'WIPi_SB7',
    'SB8': 'WIPi_SB8',
    'SB9': 'WIPi_SB9',
    'SB10': 'WIPi_SB10',
    # NT block
    'NT1': 'WIPi_NT1',
    'NT2': 'WIPi_NT2',
    'NT3': 'WIPi_NT3',
    'NT4': 'WIPi_NT4',
    'NT5': 'WIPi_NT5',
    'NT6': 'WIPi_NT6',
    # BT block
    'BT1': 'WIPi_BT1',
    'BT2': 'WIPi_BT2',
    'BT3': 'WIPi_BT3',
    'BT4': 'WIPi_BT4',
    'BT5': 'WIPi_BT5',
    'BT6': 'WIPi_BT6',

    # MP block (shared pallet feeds both)
    'MP1': 'WIPi_MP1',
    'MP2': 'WIPi_MP1',
    'MP3': 'WIPi_MP3',
    'MP4': 'WIPi_MP4',

    # FB block (shared pallet feeds both)
    'FB1': 'WIPi_FB',
    'FB2': 'WIPi_FB',
    'FB3': 'WIPi_FB',
    'FB4': 'WIPi_FB',

    # FI block
    'FI1': 'WIPi_FI',
    'FI2': 'WIPi_FI',
    'FI3': 'WIPi_FI',
    'FI4': 'WIPi_FI',

    # D&P block
    'D&P1': 'WIPi_D&P1',
    'D&P2': 'WIPi_D&P2',
    'D&P3': 'WIPi_D&P3',
    'D&P4': 'WIPi_D&P4',
}

Forklift_Capacity = 10

WC_REJECT_INTERVAL = 1305

# Probability that the two-test-unit batch fails tensile test (0.0 → always pass; 1.0 → always fail)
TT_FAIL_INTERVAL = 43200

# ── Stage-4 → Stage-4_storage ────────────────────────────────
# HDT_INCOMING_PALLET       = 36   # shells arriving *from* Stage 4
HDT_PALLET_SIZE   = 36 
CUT_SAMPLE_COUNT   = 2
# HDT_HOLD_PALLET     = 34

# ── Stage-5 merge & test ───────────────────────────────────────
FO_MERGE_CAP         = 42    # size before WIPi_UT transport
PDB_SAMPLE           = 1     # shells destroyed each PDB cycle
PDB_FAIL_INTERVAL    = 435 # time units between all destructive tests

# convenience
POST_PDB_PALLET_SIZE = FO_MERGE_CAP - PDB_SAMPLE  # = 41

MACHINE_LIST = ['FO1', 'FO2', 'FO3', 'FO4', 'UT', 'SR1', 'DB1', 'DB2', 'DB3', 'DB4', 'DB5', 'DB6', 'KN1', 'KN2', 'PDB1', 'PDB2', 'FC1', 'FC2', 'FC3', 'SP1'] #STAGE5 INVESTIGATION DELETE WHEN DONE 
