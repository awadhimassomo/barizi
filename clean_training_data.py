import json
import re
from pathlib import Path
from datetime import datetime

def clean_training_data(input_file):
    """
    Clean training data by:
    1. Removing empty or very short entries
    2. Making prompts unique by including route information
    3. Anonymizing pricing information
    4. Standardizing metadata in prompts
    """
    # Create output filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = input_file.parent / f"cleaned_{input_file.stem}_{timestamp}{input_file.suffix}"
    
    cleaned_count = 0
    removed_count = 0
    
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
        
        for line in infile:
            try:
                data = json.loads(line.strip())
                
                # Skip if instruction or response is too short
                if len(data.get('instruction', '').strip()) < 5 or len(data.get('response', '').strip()) < 100:
                    removed_count += 1
                    continue
                
                # Get metadata or create empty dict if not exists
                metadata = data.get('metadata', {})
                
                # Anonymize pricing in response
                response = data['response']
                response = re.sub(r'\$\d+\s*(?:USD)?\s*(?:per person|pp|per day|per night|per night,? per person|pppn)?', 
                               '(Contact us for current pricing)', 
                               response, 
                               flags=re.IGNORECASE)
                
                # Make instruction more specific using metadata
                instruction = data['instruction']
                
                # Add route information if available
                route = metadata.get('route', '').lower()
                if route:
                    if 'via the ' not in instruction.lower() and 'route' not in instruction.lower():
                        instruction = f"{instruction.rstrip('.')} via the {route.title()} Route"
                
                # Add duration if available
                duration = metadata.get('duration_days')
                if duration and 'day' not in instruction.lower():
                    instruction = f"{instruction.rstrip('.')} for {duration} days."
                
                # Add destination if available
                destination = metadata.get('destination', '')
                if destination and destination.lower() not in instruction.lower():
                    instruction = f"{instruction.rstrip('.')} to {destination}."
                
                # Update the data
                cleaned_data = {
                    'instruction': instruction,
                    'response': response,
                    'metadata': metadata
                }
                
                # Write cleaned data to output file
                outfile.write(json.dumps(cleaned_data, ensure_ascii=False) + '\n')
                cleaned_count += 1
                
            except json.JSONDecodeError:
                print(f"Skipping invalid JSON line: {line[:100]}...")
                removed_count += 1
                continue
    
    print(f"\nCleaning complete!")
    print(f"Processed: {cleaned_count + removed_count} records")
    print(f"Kept: {cleaned_count} records")
    print(f"Removed: {removed_count} records")
    print(f"Cleaned data saved to: {output_file}")
    return output_file

if __name__ == "__main__":
    # Example usage
    input_dir = Path(r"media/training_exports/")
    
    # Find the most recent training data file
    training_files = list(input_dir.glob("training_data_*.jsonl")) + \
                    list(input_dir.glob("sterilized_training_data_*.jsonl"))
    
    if not training_files:
        print("No training data files found in the specified directory.")
    else:
        # Get the most recent file
        latest_file = max(training_files, key=lambda x: x.stat().st_mtime)
        print(f"Processing file: {latest_file}")
        clean_training_data(latest_file)
