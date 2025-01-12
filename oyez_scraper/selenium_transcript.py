from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import json
import time

def get_case_metadata(driver, case_year, case_name):
    """
    Scrapes metadata for a Supreme Court case from Oyez.org
    
    Args:
        driver: Selenium WebDriver instance
        case_year: Year of the case (e.g., "2023")
        case_name: Partial name of the case (e.g., "Acheson")
    
    Returns:
        dict: Case metadata including:
            - title: Full case name
            - url: Oyez case URL
            - description: Case summary
            - petitioner/respondent: Parties involved
            - advocates: List of attorneys
            - facts: Facts of the case
            - question: Question presented
            - conclusion: Court's conclusion
            - oral_argument_url: URL to oral argument
            - timeline dates (granted, argued, decided)
    """
    # First get metadata from the case list page
    driver.get(f'https://www.oyez.org/cases/{case_year}')
    print(f"Loading cases list page for {case_year}...")
    time.sleep(5)
    
    # Find all case items
    case_items = driver.find_elements(By.CSS_SELECTOR, 'li[ng-repeat*="case in pager.content"]')
    print(f"Found {len(case_items)} cases")
    
    # Print all case titles for debugging
    print("\nAvailable cases:")
    for case in case_items:
        try:
            title = case.find_element(By.CSS_SELECTOR, 'h2 a').text.strip()
            print(f"- {title}")
        except:
            continue
    
    # Find the specific case we want
    target_case = None
    for case in case_items:
        try:
            title = case.find_element(By.CSS_SELECTOR, 'h2 a').text.strip()
            # Make the matching more flexible
            if any(word.lower() in title.lower() for word in case_name.split()):
                target_case = case
                print(f"\nFound target case: {title}")
                break
        except Exception as e:
            continue
    
    if not target_case:
        raise Exception(f"Could not find case containing '{case_name}'. Please check the available cases listed above.")
    
    metadata = {}
    
    try:
        # Get case title and URL from the found case
        case_link = target_case.find_element(By.CSS_SELECTOR, 'h2 a')
        metadata['title'] = case_link.text.strip()
        case_url = case_link.get_attribute('href')
        metadata['url'] = case_url
        
        # Get case description from list page
        description = target_case.find_element(By.CSS_SELECTOR, '.description')
        metadata['description'] = description.text.strip()
        
        # Now navigate to the specific case page
        driver.get(case_url)
        print("Loading case details page...")
        time.sleep(5)
        
        # Get parties
        try:
            parties = driver.find_element(By.CSS_SELECTOR, 'div.row:first-child')
            metadata['petitioner'] = parties.find_element(By.XPATH, ".//div[h3[text()='Petitioner']]").text.replace('Petitioner', '').strip()
            metadata['respondent'] = parties.find_element(By.XPATH, ".//div[h3[text()='Respondent']]").text.replace('Respondent', '').strip()
        except Exception as e:
            print(f"Error getting parties: {e}")
        
        # Get case details
        try:
            metadata['docket_no'] = driver.find_element(By.XPATH, "//div[h3[text()='Docket no.']]/text()").strip()
            metadata['decided_by'] = driver.find_element(By.XPATH, "//div[h3[text()='Decided by']]//a").text.strip()
            metadata['lower_court'] = driver.find_element(By.XPATH, "//div[h3[text()='Lower court']]").text.replace('Lower court', '').strip()
        except Exception as e:
            print(f"Error getting case details: {e}")
        
        # Get advocates
        try:
            advocates_section = driver.find_element(By.CSS_SELECTOR, 'div.subcell[ng-if="case.advocates"]')
            advocates = []
            for advocate in advocates_section.find_elements(By.CSS_SELECTOR, '.advocate'):
                name = advocate.find_element(By.CSS_SELECTOR, 'a').text.strip()
                role = advocate.find_element(By.CSS_SELECTOR, '.description').text.strip()
                advocates.append({
                    'name': name,
                    'role': role
                })
            metadata['advocates'] = advocates
        except Exception as e:
            print(f"Error getting advocates: {e}")
        
        # Get facts of the case
        try:
            facts_section = driver.find_element(By.CSS_SELECTOR, 'section.abstract[ng-if="case.facts_of_the_case"]')
            facts_paragraphs = facts_section.find_elements(By.CSS_SELECTOR, 'div.ng-binding p')
            metadata['facts'] = '\n\n'.join([p.text.strip() for p in facts_paragraphs])
        except Exception as e:
            print(f"Error getting facts: {e}")
        
        # Get question presented
        try:
            question_section = driver.find_element(By.CSS_SELECTOR, 'section.abstract[ng-if="case.question"]')
            question_paragraphs = question_section.find_elements(By.CSS_SELECTOR, 'div.ng-binding p')
            metadata['question'] = '\n\n'.join([p.text.strip() for p in question_paragraphs])
        except Exception as e:
            print(f"Error getting question: {e}")
        
        # Get conclusion
        try:
            conclusion_section = driver.find_element(By.CSS_SELECTOR, 'section.abstract div[ng-if="case.conclusion"]')
            conclusion_paragraphs = conclusion_section.find_elements(By.CSS_SELECTOR, 'p')
            metadata['conclusion'] = '\n\n'.join([p.text.strip() for p in conclusion_paragraphs])
        except Exception as e:
            print(f"Error getting conclusion: {e}")
        
        # Add oral argument URL
        try:
            # Look for the oral argument link with the specific attributes
            oral_argument_link = driver.find_element(
                By.CSS_SELECTOR, 
                'a[data-gtm-category="Audios"][data-gtm-type="click"][iframe-url*="oral_argument_audio"]'
            )
            # Get the iframe URL which contains the actual player URL
            iframe_url = oral_argument_link.get_attribute('iframe-url')
            metadata['oral_argument_url'] = iframe_url
            print(f"Found oral argument URL: {iframe_url}")
        except Exception as e:
            print(f"Error getting oral argument URL: {e}")
            # Try alternative method
            try:
                # Look for any link containing oral_argument_audio in the iframe-url
                oral_argument_link = driver.find_element(
                    By.CSS_SELECTOR,
                    'a[iframe-url*="oral_argument_audio"]'
                )
                iframe_url = oral_argument_link.get_attribute('iframe-url')
                metadata['oral_argument_url'] = iframe_url
                print(f"Found oral argument URL (alternative method): {iframe_url}")
            except Exception as e2:
                print(f"Error getting oral argument URL (alternative method): {e2}")
                metadata['oral_argument_url'] = None
            
        # Get case details from the timeline section
        try:
            timeline_section = driver.find_element(By.CSS_SELECTOR, 'div.cell:has(div.subcell)')
            
            # Get citation
            try:
                citation_element = timeline_section.find_element(
                    By.CSS_SELECTOR, 
                    'div.subcell[ng-if="case.citation"] span.ng-binding'
                )
                metadata['citation'] = citation_element.text.strip()
            except Exception as e:
                print(f"Error getting citation: {e}")
                metadata['citation'] = None
            
            # Get timeline dates (Granted, Argued, Decided)
            timeline_items = timeline_section.find_elements(
                By.CSS_SELECTOR, 
                'div.subcell.ng-binding.ng-scope'
            )
            
            for item in timeline_items:
                try:
                    # Get the header (Granted, Argued, or Decided)
                    header = item.find_element(By.CSS_SELECTOR, 'h3').text.strip().lower()
                    # Get the date
                    date = item.find_element(By.CSS_SELECTOR, 'div.ng-binding.ng-scope').text.strip()
                    metadata[header] = date
                except Exception as e:
                    print(f"Error getting {header} date: {e}")
                    metadata[header] = None
                    
        except Exception as e:
            print(f"Error getting timeline details: {e}")
        
    except Exception as e:
        print(f"Error getting specific metadata: {e}")
    
    print("\nMetadata found:")
    for key, value in metadata.items():
        if isinstance(value, list):
            print(f"\n{key}:")
            for item in value:
                print(f"  - {item}")
        else:
            print(f"{key}: {value}")
    
    return metadata

def get_transcript_with_selenium(case_year="2023", case_name="Acheson Hotels", full_transcript=False):
    """
    Scrapes oral argument transcript from Oyez.org
    
    Args:
        case_year: Year of the case (e.g., "2023")
        case_name: Partial name of the case (e.g., "Acheson")
        full_transcript: If True, gets entire transcript. If False, gets first 3 blocks (test mode)
                        The output filename will include '_test' or '_full' accordingly
    
    Output:
        Saves a JSON file containing:
        - Case metadata
        - Transcript entries with:
            - speaker: Name of the speaker
            - text: What was said
            - start_time/stop_time: Timing information
    
    Note:
        - The script handles Oyez's dynamic loading by clicking each text block
        - Uses retries and waits to ensure content loads properly
        - Saves progress information to console
    """
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 20)
    
    try:
        # First get the case metadata
        metadata = get_case_metadata(driver, case_year, case_name)
        
        # Get the oral argument URL from metadata
        oral_argument_url = metadata.get('oral_argument_url')
        if not oral_argument_url:
            print("No oral argument URL found")
            return
            
        # Load the transcript page
        driver.get(oral_argument_url)
        print("\nLoading transcript page...")
        time.sleep(5)  # Initial wait
        
        # Wait for at least one text block to be present
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'p.ng-binding.ng-scope.ng-isolate-scope')))
            print("Initial transcript block found")
        except Exception as e:
            print("Timeout waiting for transcript blocks, trying longer wait...")
            time.sleep(10)  # Extra wait if needed
        
        # Get text blocks with retry
        max_retries = 3
        for attempt in range(max_retries):
            blocks = driver.find_elements(By.CSS_SELECTOR, 'p.ng-binding.ng-scope.ng-isolate-scope')
            if blocks:
                print(f"Found {len(blocks)} transcript blocks")
                break
            else:
                print(f"Attempt {attempt + 1}: No transcript blocks found, waiting...")
                time.sleep(5)
        
        if not blocks:
            raise Exception("Could not load transcript blocks after multiple attempts")
        
        # TRANSCRIPT CONTROL
        # To get the full transcript, set full_transcript=True when calling this function
        # Example: get_transcript_with_selenium(case_year="2023", case_name="Acheson Hotels", full_transcript=True)
        if not full_transcript:
            print("Getting first 3 blocks only (TEST MODE)")
            blocks = blocks[:3]  # Get only first 3 blocks for testing
        else:
            print(f"Getting all {len(blocks)} blocks (FULL TRANSCRIPT MODE)")
        
        transcript = []
        current_speaker = None
        
        for i, block in enumerate(blocks):
            try:
                # Click block to reveal text (required by Oyez's interface)
                driver.execute_script("arguments[0].click();", block)
                time.sleep(0.1)  # Reduced from 0.2 to 0.1 seconds
                
                text = block.text.strip()
                print(f"\nBlock {i+1}/{len(blocks)} text: {text[:100]}")
                
                start_time = block.get_attribute('start-time')
                stop_time = block.get_attribute('stop-time')
                
                # Find the speaker for this block
                speaker = driver.execute_script("""
                    function findSpeaker(element) {
                        let turn = element.closest('.transcript-turn');
                        if (turn) {
                            let label = turn.querySelector('h4.ng-binding');
                            if (label) {
                                return label.textContent;
                            }
                        }
                        return null;
                    }
                    return findSpeaker(arguments[0]);
                """, block)
                
                if speaker:
                    current_speaker = speaker.strip()
                elif not current_speaker:
                    # Fallback: try to find any speaker if none found
                    speakers = driver.find_elements(By.CSS_SELECTOR, 'h4.ng-binding')
                    if speakers:
                        current_speaker = speakers[0].text.strip()
                
                if text and current_speaker:
                    entry = {
                        'speaker': current_speaker,
                        'text': text,
                        'start_time': start_time,
                        'stop_time': stop_time
                    }
                    transcript.append(entry)
                    if i % 10 == 0:  # Print progress every 10 blocks
                        print(f"Progress: {i+1}/{len(blocks)} blocks processed")
            
            except Exception as e:
                print(f"Error processing block {i+1}: {e}")
                continue
        
        # Create result with mode indicator
        result = {
            'case_name': metadata['title'],
            'argument_date': metadata.get('argued'),
            'metadata': metadata,
            'transcript': transcript,
            'transcript_mode': 'TEST (first 3 blocks)' if not full_transcript else 'FULL'
        }
        
        # Save to file
        safe_case_name = metadata['title'].replace(' ', '_').replace(',', '').replace('.', '').replace('v', 'v')
        mode_suffix = '_test' if not full_transcript else '_full'
        filename = f'{safe_case_name}_transcript{mode_suffix}.json'
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\nSaved {len(transcript)} transcript entries to {filename}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    # Single case processing
    get_transcript_with_selenium(
        case_year="2023",
        case_name="Acheson",  # Just need part of the name
        full_transcript=False
    )