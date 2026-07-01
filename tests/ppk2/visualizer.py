import os
import glob
import pandas as pd
import matplotlib.pyplot as plt

# Get the script directory to handle relative paths reliably
script_dir = os.path.dirname(os.path.abspath(__file__))

print(f"Script base directory: {script_dir}")
rel_folder_path = input("Enter the relative path to the folder containing CSV files (e.g., 'measurements'): ")

# Resolve absolute path to the target directory
target_dir = os.path.abspath(os.path.join(script_dir, rel_folder_path))

# Verify if the directory exists
if not os.path.exists(target_dir):
    print(f"Error: The directory '{target_dir}' does not exist!")
    exit(1)

# Find all CSV files in the target directory
csv_files = glob.glob(os.path.join(target_dir, "*.csv"))

if not csv_files:
    print(f"No CSV files found in directory '{target_dir}'.")
    exit(0)

print(f"Found {len(csv_files)} CSV file(s). Processing starts...\n")

# Iterate through all found CSV files
for file_path in csv_files:
    file_name = os.path.basename(file_path)
    print(f"Processing: {file_name} ...")
    
    try:
        # Load the CSV data
        df = pd.read_csv(file_path)
        
        # Validate expected PPK2 column structure
        if 'Timestamp(ms)' not in df.columns or 'Current(uA)' not in df.columns:
            print(f"-> Skipped: '{file_name}' does not match the expected PPK2 column format.")
            continue
            
        # Initialize the subplots
        fig, ax = plt.subplots(figsize=(10, 5))
        
        # Scale data for better readability in the plot
        time_s = df['Timestamp(ms)'] / 1000.0
        current_ma = df['Current(uA)'] / 1000.0
        
        # Plot current profile
        ax.plot(time_s, current_ma, label='Stromverbrauch in mA', color='#1f77b4', linewidth=1)
        
        # Configure axis labels and title
        ax.set_xlabel('Zeit (s)', fontsize=12)
        ax.set_ylabel('Strom (mA)', fontsize=12)
        ax.set_title(f"PPK2 Messungen", fontsize=13, fontweight='bold')
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.legend(loc='upper right')
        
        # Optimize layout spacing
        plt.tight_layout()
        
        # Generate output image path (replace .csv extension with .png)
        output_image_name = os.path.splitext(file_name)[0] + '.png'
        output_image_path = os.path.join(target_dir, output_image_name)
        
        # Save the plot and release memory
        plt.savefig(output_image_path, dpi=300)
        plt.close()
        print(f"-> Successfully saved as: {output_image_name}")
        
    except Exception as e:
        print(f"-> Error processing '{file_name}': {e}")

print("\nAll files have been successfully processed!")