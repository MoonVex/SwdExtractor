import re
import pandas as pd
import os

IoBit=1
ClkBit=0
def read_pat_file(file_path):
    """Read the contents of the PAT file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.readlines()

def extract_valid_characters(pat_data):
    """Extract valid characters from each line of the file using the pattern '* xxxx *'."""
    valid_char_pattern = re.compile(r'\* ([01HLX]{4}) \*')
    extracted_data = []
    for line in pat_data:
        match = valid_char_pattern.search(line)
        if match:
            extracted_data.append(match.group(1))
    return extracted_data

def extract_swd_instructions(data, cycles_required=46):
    """ Extract complete SWD instructions from multiple cycles. """
    instructions = []
    reset_counter = 0
    current_instruction = []

    SwdExec=0
    
    for value in data:
        if value[IoBit]=='0' or value[IoBit]=='1' :
            swdio = int(value[IoBit]) 
        if value[IoBit]=='L' or value[IoBit]=='H' or value[IoBit]=='X' :
            swdio = value[IoBit]
        swdclk = int(value[ClkBit])  # SWDCLK (0-based index, but 1-based given in requirements)

        if (SwdExec==0)&(swdclk==0)&(swdio==1):
            SwdExec=1
        if swdio == 1:
            reset_counter += 1
        else:
            reset_counter = 0

        # Detect reset signal if 50 consecutive high levels on SWDIO
        if reset_counter >= 50:
            instructions.append({
                'Type': 'Reset',
                'Details': '50 consecutive high levels detected on SWDIO'
            })
            reset_counter = 0
            current_instruction = []
            continue

        if (swdclk==0)&(SwdExec==1):current_instruction.append(value)

        if len(current_instruction) == cycles_required:
            # Extract SWD protocol components from the 46-bit instruction
            start = int(current_instruction[0][IoBit])
            apndp = int(current_instruction[1][IoBit])
            rnw = int(current_instruction[2][IoBit])
            a2 = int(current_instruction[3][IoBit])
            a3 = int(current_instruction[4][IoBit])
            parity1 = int(current_instruction[5][IoBit])
            stop = int(current_instruction[6][IoBit])  # Stop bit is the last bit in the 46-bit instruction
            park = int(current_instruction[7][IoBit])  
            trn1 = int(current_instruction[8][IoBit])  
            ack = current_instruction[9][IoBit]+current_instruction[10][IoBit]+current_instruction[11][IoBit]

            if rnw == 0:
                trn2 = current_instruction[12][IoBit]
                wdata = '0b' + ''.join([cycle[1] for cycle in current_instruction[13:45]])[::-1]
                parity2 = current_instruction[45][IoBit]
            else:
                trn2 = current_instruction[45][IoBit]
                wdata = '0b' + ''.join([cycle[1] for cycle in current_instruction[12:44]]) [::-1]
                parity2 = current_instruction[44][IoBit]

            instructions.append({
                'Start': start,
                'APnDP': apndp,
                'RnW': rnw,
                'A2': a2,
                'A3': a3,
                'Parity1': parity1,
                'Stop': stop,
                'Park': park,
                'Trn1': trn1,
                'ACK': ack,
                'Trn2': trn2,
                'WDATA': wdata,
                'Parity2': parity2
            })
            SwdExec=0
            current_instruction = []
    return instructions

def save_to_csv(instructions, output_file_path):
    """Convert the extracted instructions to a DataFrame and save it as a CSV file."""
    df = pd.DataFrame(instructions)
    df.to_csv(output_file_path, index=False)

def process_all_pat_files(input_directory, output_directory):
    """Process all .PAT files in the specified directory."""
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    for filename in os.listdir(input_directory):
        if filename.lower().endswith(('.pat', '.PAT')):
            input_path = os.path.join(input_directory, filename)
            output_filename = f"{os.path.splitext(filename)[0]}_SWDextracted.csv"
            output_path = os.path.join(output_directory, output_filename)
            
            print(f"Processing file: {input_path}")
            pat_data = read_pat_file(input_path)
            extracted_data = extract_valid_characters(pat_data)
            swd_instructions = extract_swd_instructions(extracted_data)
            save_to_csv(swd_instructions, output_path)
            print(f"SWD instructions extracted and saved to {output_path}")

def main():
    input_directory = 'input_pats'  # Directory containing PAT files
    output_directory = 'output_csvs'  # Directory to save output CSV files
    
    process_all_pat_files(input_directory, output_directory)

if __name__ == "__main__":
    main()
