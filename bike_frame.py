import os
import openai
import tiktoken
from itertools import product
from dotenv import load_dotenv, find_dotenv

def generate_prompt(json_data):
    
    title = json_data.get(f"title", "")
    publisher_title = json_data.get(f"ptitle", "")

    system_message = """\
```python
Class BikeFrame:
    '''
    The BikeFrame class analyzes news headlines related to cyclists. It determines if the headline is related to an accident, 
    identifies who might be at fault, and assesses the perception towards the cyclist.
    '''
    def __init__(self, headline, source_info):
        self.headline = headline  # Initialize the headline attribute
        self.source_info = source_info  # Initialize the source_info attribute
        
    def detect_accident_in_headline(self):
        '''
        Analyze the headline's content to determine if it explicitly mentions an accident, 
        involving a collision, injury, or fatality from a crash.
        Provide a rationale for classifying the headline as either accident-related or not.
        Returns:
            Tuple[bool, str]: A tuple containing a boolean to indicate whether the headline directly refers to an actual accident, 
            and a string explaining the reasoning behind this classification.
        '''
        accident_related, reason = self.analyze_semantic_content()
        return accident_related, reason
    
    def conduct_behavior_analysis(self):
        '''
          Conducts a behavior analysis of all parties mentioned in the headline, 
          to identify specific actions or failures that contributed to the collision, injury, or fatality from a crash.
          Returns:
              dict: A dictionary containing behaviors associated with each party mentioned in the headline.
          '''
          # Initialize a dictionary to store the behavior analysis results for each party.
          behavior_dict = {}
          
          parties = self.extract_parties_from_headline()
          for party in parties:
              behavior = self.extract_behavior_for_party(party)
              # Convert passive constructions to active for each party's behavior
              behavior_dict[party] = convert_passive_to_active(behavior)
          return behavior_dict
    
    def is_cyclist(self, description):
        '''
        Determines if the provided description mentions cyclists in a context not related to motorcycles.
        Returns:
            bool: True if the description mentions cyclists (excluding motorcyclists), otherwise False.
        '''
        cyclist_pattern = r'\b([a-zA-Z]*cyclist[s]?|[a-zA-Z]*biker[s]?|bicycle|bike|cycling|bicycling|pedal(ing)?|mountain|road|touring|BMX|[a-zA-Z]*velo)\b'
        motorcycle_exclusion = r'\b(moto(cyc|bike)|motorbike|motorcycle|biker gang|Harley|chopper|superbike)\b'
        
        if re.search(motorcycle_exclusion, description, re.IGNORECASE):
            return False
        return bool(re.search(cyclist_pattern, description, re.IGNORECASE))
        
    def analyze_fault_in_accident(self):
        '''
        Analyze a headline to determine if it is related to an accident and identify who is at fault.
        Returns:
            str: 'Yes' if the headline is related to an accident, 'No' otherwise.
            str: Indicates the party at fault, categorized as either 'Cyclist', 'Other', or 'Unknown' if fault cannot be determined or the headline is not accident-related.
            dict: Describes the behaviors of parties involved in the headline, mapped to their respective descriptions.
            dict: Provides tone analysis results for each party, mapping their description to the tone implied about them in the headline.
        '''
        # Step 1: Check if the headline is related to an accident.
        accident_related, accident_rationale = self.detect_accident_in_headline()
        accident_label = 'Yes' if accident_related else 'No'
        print(f"Is the headline discussing an accident? {accident_label}, based on rationale: {accident_rationale}")
        
        # Step 2: Check parties' behaviors in headline
        party_behaviors = self.conduct_behavior_analysis()
        print(f"Party behaviors: {party_behaviors}")
        
        # Initialize dictionaries for storing law violations and tone analysis results
        law_violations = {}
        tone_analysis_results = {}

        # Step 3: Evaluate each party's behavior to determine if they have actively violated traffic laws, 
        # and provide a clear rationale for each determination made.
        for party, behavior in party_behaviors.items():
            violation_occurred, law_rationale = self.assess_traffic_law_violations_for_party(party, behavior)
            law_violations[party] = (violation_occurred, law_rationale)
            print(f"Law analysis: {party} {'violated the law' if violation_occurred else 'did not violate the law'}. Rationale: {law_rationale}")

        # Step 4: Evaluate the tone of the headline to aid in determining fault attribution for each party involved in the incident.
        for party in party_behaviors.keys():
            tone_result, tone_rationale = self.analyze_tone_for_party(party)
            tone_analysis_results[party] = (tone_result, tone_rationale)
            print(f"Tone analysis: {party} is described as '{tone_result}', suggesting {tone_rationale}.")
            
        if accident_related:
            # Step 5: Identify the party most likely at fault in the accident.
            # Use a combination of behavior analysis, legal violations, and tone assessments to determine fault.
            most_likely_fault = self.determine_most_likely_fault(party_behaviors, law_violations, tone_analysis_results)
            print(f"Most likely accident-related fault party: {most_likely_fault}")  
            
            # Check if the most likely fault party is not 'Unknown'
            if most_likely_fault != 'Unknown':
                # Check if the most likely fault party is a cyclist
                if self.is_cyclist(most_likely_fault):
                    fault_label = "Cyclist"
                else:
                    fault_label = "Other" 
             print(f"Therefore, the fault is attributed to {fault_label}.")
             
        else:
            print("No accident, hence, fault is labeled as 'Unknown'.")
            fault_label = 'Unknown'
            
        return accident_label, fault_label, party_behaviors, tone_analysis_results

    def assess_cyclist_perception(self):
        ''
        Predict the final perception towards cyclists based on a headline and the editorial stance of the news source.        
        Returns:
            str: The perception towards the cyclist categorized as 'Negative', 'Positive', or 'Neutral'.
        '''
        # Step 1: Extract source from input text.
        print("Extracted News Source:", self.source)
        
        # Step 2: Analyze fault in the accident and obtain accident_label, fault_label, and party_behaviors.
        accident_label, fault_label, party_behaviors, tone_analysis_results= self.analyze_fault_in_accident()
         
        # Step 3: Analyze how the specified news agency reports on cyclists.
        # Returns: str: A summary of the analysis detailing the news agency's coverage on cyclists.
        prompt = (
            f"How does the news agency '{self.source}' typically cover stories related to cyclists, "
            f"considering both past and present editorial stances? Assess the tone, language, "
            f"and common themes in their reporting to discern any potential biases or recurring patterns."
        )
        source_analysis_result = self.analyze_news_coverage(prompt)
        print("News Coverage Analysis Result:", source_analysis_result)
        
        # Step 4: Analyze the perception towards cyclists based on a headline and provide a detailed reason for classification.
        #  Criteria for perception towards cyclists include:
        criteria = {
            "negative": "Headlines that attribute the cause of an accident directly to the cyclist’s behavior, 
                         suggesting that the cyclist is responsible for the accident or injury that occurs.",
            "positive": "Headlines that portray cyclists in a positive way or as victims of incidents, casting them 
                        in a favorable or sympathetic light, emphasizing their vulnerability and evoking sympathy from readers.",
            "neutral": "Headlines that deliver information about cyclists in an impartial and objective manner, 
                        without conveying judgment or invoking significant emotional response to the cyclist's actions."
                }         
                
        # Generate intermediate rationale based on the headline and criteria
        intermediate_rationale = self.generate_cyclist_perception_rationale(headline, criteria)
        print(f"Intermediate Rationale: {intermediate_rationale}")

        # Step 5: Determine the final perception towards cyclists based on comprehensive analysis results, according to criteria.
        perception_label = self.predict_final_perception(intermediate_rationale, party_behaviors, tone_analysis_results, source_analysis_result, criteria)
        return accident_label, fault_label, perception_label

    def analyze_headline(self):
        '''
        Analyze a headline to determine its relation to an accident, identify who is at fault, and then assess the perception towards the cyclists.
        Returns:
            Tuple[str, str，str]:
                - accident: 'Yes' or 'No'.
                - fault: 'Cyclist', 'Other', or 'Unknown'.
                - perception: 'Negative', 'Positive', or 'Neutral'.
        '''
        print(f"Starting analysis of the headline: {self.headline}")
        accident, fault, perception = self.assess_cyclist_perception()
        
        return (accident, fault, perception)
```
"""

    user_input = f"""\
```python
input_text =  "{title}"
publisher_title =  "{publisher_title}"
bike_frame = BikeFrame(input_text, publisher_title)
final_answer = bike_frame.analyze_headline()
print("Final answer:"+ final_answer)
``` 

# Instruction: 
Generate the expected execution output (output from all print() functions) of the code. 
You don't have to actually run the code and do not care about 'not implemented error'.
"""


###########################################################################################
# 
#                                    Few-Shot Learning 
# 
###########################################################################################

###########################################################################################
#   No
###########################################################################################
    user_message1 = """\
```python
input_text =  "Durango man spared jail time over road rage with cyclist - The Journal"
publisher_title =  "The Journal"
bike_frame = BikeFrame(input_text, publisher_title)
final_answer = bike_frame.analyze_headline()
print("Final answer:"+ final_answer)
``` 

# Instruction: 
Generate the expected execution output (output from all print() functions) of the code. 
You don't have to actually run the code and do not care about 'not implemented error'.
"""
    assistant_message1 = """\
Starting analysis of the headline: Durango man spared jail time over road rage with cyclist - The Journal
Extracted News Source: The Journal
Is the headline discussing an accident? No, based on rationale: The headline mentions road rage involving a cyclist, but it does not specify that a crash or injury occurred.
Party behaviors: {'Durango man': 'aggressive behavior', 'cyclist': 'victim of road rage'}
Law analysis: Durango man violated the law. Rationale: Road rage is typically considered a violation of traffic laws.
Law analysis: cyclist did not violate the law. Rationale: The headline suggests the cyclist was a victim, not the perpetrator.
Tone analysis: Durango man is described as 'road rage', suggesting negative implications.
Tone analysis: cyclist is described as 'victim', suggesting sympathetic implications.
No accident, hence, fault is labeled as 'Unknown'.
News Coverage Analysis Result: The Journal typically covers stories related to cyclists with a focus on individual responsibility and safety. The tone is often straightforward and factual, avoiding sensationalism even in the context of incidents like road rage or accidents. There is no clear bias against cyclists; the coverage tends to present the facts of each case without overly sympathetic or critical angles towards any party involved.
Intermediate Rationale: The headline suggests the Durango man showed negative behavior in a road rage with a cyclist, casting the cyclist as the victim and evoking sympathy for them. Therefore, it implies a positive perception towards cyclist.
Final answer: ('No', 'Unknown', 'Positive')""" # potential accident, not happened


    user_message2 = """\
```python
input_text =  "Durham mum narrowly missed cyclist and clocked 70mph in 30 zones during police pursuit - Chronicle Live"
publisher_title =  "Chronicle Live"
bike_frame = BikeFrame(input_text, publisher_title)
final_answer = bike_frame.analyze_headline()
print("Final answer:"+ final_answer)
``` 

# Instruction: 
Generate the expected execution output (output from all print() functions) of the code. 
You don't have to actually run the code and do not care about 'not implemented error'.
"""
    assistant_message2 = """\
Starting analysis of the headline: Durham mum narrowly missed cyclist and clocked 70mph in 30 zones during police pursuit - Chronicle Live
Extracted News Source: Chronicle Live
Is the headline discussing an accident? No, based on rationale: The headline mentions a near miss with a cyclist and a high-speed pursuit, indicating that no actual collision or crash occurred.
Party behaviors: {'Durham mum': 'narrowly missed cyclist and clocked 70mph in 30 zones during police pursuit','cyclist': 'narrowly missed'}
Law analysis: Durham mum violated the law. Rationale: Speeding and evading police are clear violations of traffic laws.
Law analysis: cyclist did not violate the law. Rationale: The cyclist was nearly hit but did not contribute to the dangerous situation.
Tone analysis: Durham mum is described as 'reckless', suggesting negative implications.
Tone analysis: cyclist is described as 'endangered', suggesting sympathetic implications.
No accident, hence, fault is labeled as 'Unknown'.
News Coverage Analysis Result: "Chronicle Live" tends to report on cycling-related stories with a focus on practical impacts and community relevance. For instance, their coverage on the temporary closure of the Tyne Pedestrian and Cyclist Tunnels highlights logistical information like the provision of a replacement bus service, emphasizing the direct effects on commuters and cyclists. 
Intermediate Rationale: The headline portrays the cyclist as being narrowly missed by a speeding vehicle, highlighting their vulnerability in the situation. This depiction of the cyclist as a victim of a potentially dangerous incident may evoke empathy from readers, leading to a positive perception of the cyclist.
Final answer: ('No', 'Unknown', 'Positive')""" # potential accident, not happened
    
    
    user_message3 = """\
```python
input_text =  "Man accused of assaulting teen cyclist in South Davis - Davis Enterprise"
publisher_title =  "Davis Enterprise"
bike_frame = BikeFrame(input_text, publisher_title)
final_answer = bike_frame.analyze_headline()
print("Final answer:"+ final_answer)
``` 

# Instruction: 
Generate the expected execution output (output from all print() functions) of the code. 
You don't have to actually run the code and do not care about 'not implemented error'.
"""
    assistant_message3 = """\
Starting analysis of the headline: Man accused of assaulting teen cyclist in South Davis - Davis Enterprise
Extracted News Source: Davis Enterprise
Is the headline discussing an accident? No, based on rationale: The headline indicates an assault, which is a criminal act, but not an accident, because there's no mention of a collision or injury resulting from a crash.
Party behaviors: {'Man': 'accused of assaulting', 'teen cyclist': 'victim of assault'}
Law analysis: Man violated the law. Rationale: Assaulting someone is a clear violation of criminal laws.
Law analysis: teen cyclist did not violate the law. Rationale: The headline suggests the teen cyclist was the victim of the assault.
Tone analysis: Man is described as 'aggressive', suggesting negative implications.
Tone analysis: teen cyclist is described as 'victim', suggesting sympathetic implications.
No accident, hence, fault is labeled as 'Unknown'.
News Coverage Analysis Result: The Davis Enterprise generally covers stories related to cyclists with a focus on community impact and safety issues, often featuring detailed accounts of incidents and developments that affect local cyclists. The reporting tends to adopt a straightforward and informative tone, aiming to keep the community well-informed about cycling infrastructure and events. This approach underlines a commitment to providing practical information without sensationalizing the issues involved.
Intermediate Rationale: The headline focuses on the accusation of assault against a teen cyclist, framing the cyclist as a victim. This portrayal likely generates sympathy for the cyclist, indicating a positive perception towards the cyclist.
Final answer: ('No', 'Unknown', 'Positive')""" # criminal events

    
    user_message4 = """\
```python
input_text =  "New driver 'traumatised' after cyclist appears from blind spot and dashes across road - STOMP"
publisher_title =  "STOMP"
bike_frame = BikeFrame(input_text, publisher_title)
final_answer = bike_frame.analyze_headline()
print("Final answer:"+ final_answer)
``` 

# Instruction: 
Generate the expected execution output (output from all print() functions) of the code. 
You don't have to actually run the code and do not care about 'not implemented error'.
"""
    assistant_message4 = """\
Starting analysis of the headline: New driver 'traumatised' after cyclist appears from blind spot and dashes across road - STOMP
Extracted News Source: STOMP
Is the headline discussing an accident? No, based on rationale: The use of 'traumatised' in double quotes indicates sarcasm, suggesting that there is no actual crash occurred.
Party behaviors: {'cyclist': 'appears from blind spot and dashes across road', 'driver': 'traumatised'}
Law analysis: cyclist did not violate the law. Rationale: The headline does not provide sufficient detail to determine if the cyclist violated any traffic laws.
Law analysis: driver did not violate the law. Rationale: Being 'traumatised' is a reaction, not a behavior indicating a violation of traffic laws.
Tone analysis: cyclist is described as 'reckless', suggesting the headline portrays the cyclist's actions negatively.
Tone analysis: driver is described as 'victim', suggesting the headline evokes sympathy for the driver.
No accident, hence, fault is labeled as 'Unknown'.
News Coverage Analysis Result: STOMP Singapore often covers cyclist-related stories with a sensational and provocative tone, focusing on conflicts, accidents, and unusual incidents involving cyclists. The language tends to emphasize drama and conflict, which can attract a lot of reader attention and engagement. Common themes include road altercations between cyclists and drivers, legal consequences for traffic violations, and the broader implications of these incidents on public safety and urban cycling policies.
Intermediate Rationale: Based on the headline's focus on the cyclist's sudden appearance and action, it suggests a negative perception towards the cyclist, emphasizing the potential danger they posed to the driver. Therefore, it implies a negative perception towards cyclist.
Final answer: ('No', 'Unknown', 'Negative')""" # sarcasm， not realy happened 
    
    
    user_message5 = """\
```python
input_text =  "Ribble Ultra Road launch: all-new aero bike with unique bars - Cyclist"
publisher_title =  "Cyclist"
bike_frame = BikeFrame(input_text, publisher_title)
final_answer = bike_frame.analyze_headline()
print("Final answer:"+ final_answer)
``` 

# Instruction: 
Generate the expected execution output (output from all print() functions) of the code. 
You don't have to actually run the code and do not care about 'not implemented error'.
"""
    assistant_message5 = """\
Starting analysis of the headline: Ribble Ultra Road launch: all-new aero bike with unique bars - Cyclist
Extracted News Source: Cyclist
Is the headline discussing an accident? No, based on rationale: The headline does not explicitly mention an accident, collision, injury, or fatality.
Party behaviors: {}
News Coverage Analysis Result: The news agency 'Cyclist' typically covers stories related to cyclists in a manner that is informative and enthusiast-focused, often highlighting advancements in cycling technology, achievements within the cycling community, and issues pertinent to cyclists. The tone is generally positive and supportive, aiming to foster a strong sense of community among its readership.
Intermediate Rationale: The headline does not directly attribute the cause of an accident to the cyclist’s behavior, nor does it portray cyclists in a negative light. Given the context of a product launch, the headline is focused on introducing a new bicycle model, which falls outside the typical criteria for assessing perception towards cyclists based on accident-related content. Therefore, it implies a neutral perception towards cyclist.
Final answer:('No', 'Unknown', 'Neutral')""" # off-topic neutral
    
    
    user_message6 = """\
```python
input_text =  "Cyclist dies after collapsing at Loveland Pass during Triple Bypass event - Summit Daily News"
publisher_title =  "Summit Daily News"
bike_frame = BikeFrame(input_text, publisher_title)
final_answer = bike_frame.analyze_headline()
print("Final answer:"+ final_answer)
``` 

# Instruction: 
Generate the expected execution output (output from all print() functions) of the code. 
You don't have to actually run the code and do not care about 'not implemented error'.
"""
    assistant_message6 = """\
Starting analysis of the headline: Cyclist dies after collapsing at Loveland Pass during Triple Bypass event - Summit Daily News
Extracted News Source: Summit Daily News
Is the headline discussing an accident?  No, based on rationale: The headline mentions a cyclist's death after collapsing, indicating a tragic event during a cycling event. But, this injury 'dies' is not the result of a collision or crash-related accident, and therefore it's not considered an accident.
Party behaviors: {'Cyclist': 'collapsing at Loveland Pass during Triple Bypass event'}
Law analysis: Cyclist did not violate the law. Rationale: Collapsing during an event is not a violation of law but a health-related incident.
Tone analysis: Cyclist is described as 'victim', suggesting sympathetic implications.
No accident, hence, fault is labeled as 'Unknown'.
News Coverage Analysis Result: Summit Daily News typically covers stories related to cyclists with a focus on community impact and safety. Their reporting on incidents involving cyclists, such as traffic accidents, is factual and thorough, providing details about the events without sensationalism. The tone is generally informative, aimed at keeping the local community aware of safety concerns and developments that affect cyclists. 
Intermediate Rationale: The headline emphasizes the word "dies," which portrays the cyclist as a victim of unfortunate circumstances, which likely evoking sympathy for the cyclist and concern for safety during such events, leading to a positive perception of the cyclist.
Final answer: ('No', 'Unknown', 'Positive')""" # injure not caused by accident  (dies)
    
    
    user_message7 = """\
```python
input_text =  "Para-cyclist Ablinger hospitalised following race training accident - Insidethegames.biz"
publisher_title =  "Insidethegames.biz"
bike_frame = BikeFrame(input_text, publisher_title)
final_answer = bike_frame.analyze_headline()
print("Final answer:"+ final_answer)
``` 

# Instruction: 
Generate the expected execution output (output from all print() functions) of the code. 
You don't have to actually run the code and do not care about 'not implemented error'.
"""
    
    assistant_message7 = """\
Starting analysis of the headline: Para-cyclist Ablinger hospitalised following race training accident - Insidethegames.biz
Extracted News Source: Insidethegames.biz
Is the headline discussing an accident? No, based on rationale: The headline mentions a race training accident resulting in a para-cyclist being hospitalized. However, since it's not explicitly stated that the injury was caused by a crash or collision. Therefore, it's not classified as an accident.
Party behaviors: {'Para-cyclist Ablinger': 'hospitalised following training accident'}
Law analysis: Para-cyclist Ablinger did not violate the law. Rationale: Being hospitalized after an accident does not imply a violation of traffic laws.
Tone analysis: Para-cyclist Ablinger is described as 'hospitalised', suggesting a 'victim' and sympathetic portrayal, which implies a positive perception.
No accident, hence, fault is labeled as 'Unknown'.
News Coverage Analysis Result: Insidethegames.biz typically reports on sports-related incidents with a focus on athlete well-being and performance, often highlighting the challenges and risks associated with competitive sports like cycling. The tone is generally informative and supportive, emphasizing the dedication and resilience of athletes.
Intermediate Rationale: The headline focuses on the para-cyclist's hospitalization following a training accident, evoking sympathy and concern for the athlete's well-being. The portrayal of the para-cyclist as a victim of the accident suggests a positive perception towards the cyclist.
Final answer:('No', 'Unknown', 'Positive')"""# injure not caused by accident (hospitalised)
    
    user_message8 = """\
```python
input_text =  "Cyclist dies after falling from bridge into Columbia River near Golden - Calgary Herald"
publisher_title =  "Calgary Herald"
bike_frame = BikeFrame(input_text, publisher_title)
final_answer = bike_frame.analyze_headline()
print("Final answer:"+ final_answer)
``` 

# Instruction: 
Generate the expected execution output (output from all print() functions) of the code. 
You don't have to actually run the code and do not care about 'not implemented error'.
"""
    
    assistant_message8 = """\
Starting analysis of the headline: Cyclist dies after falling from bridge into Columbia River near Golden - Calgary Herald
Extracted News Source: Calgary Herald
Is the headline discussing an accident? No, based on rationale: The headline suggests that a cyclist fell from a bridge into the Columbia River near Golden and died. Since the injury wasn't caused by a crash or collision, it's not classified as an accident.
Party behaviors: {'Cyclist': 'dies after falling from bridge into Columbia River near Golden'}
Law analysis: Cyclist did not violate the law. Rationale: Falling from a bridge is not a violation of traffic laws.
Tone analysis: Cyclist is described as 'dies' and 'victim', suggesting a tragic outcome and evoking sympathy, which implies a positive perception.
No accident, hence, fault is labeled as 'Unknown'.
News Coverage Analysis Result: The Calgary Herald typically covers cycling incidents with a focus on factual reporting and community impact, often highlighting safety concerns and the consequences of accidents without strong bias.
Intermediate Rationale: The headline reports on a tragic incident where a cyclist died after falling from a bridge, emphasizing the unfortunate outcome. The portrayal of the Cyclist as a victim of the accident suggests a positive perception towards the cyclist.
Final answer:('No', 'Unknown', 'Positive')""" # injure not caused by accident (dies)
    
###########################################################################################
#   Yes
###########################################################################################
    user_message9 = """\
```python
input_text =  "Greyhound Retail Park: Police hunt cyclist after crash | Echo - Echo"
publisher_title =  "Echo"
bike_frame = BikeFrame(input_text, publisher_title)
final_answer = bike_frame.analyze_headline()
print("Final answer:"+ final_answer)
``` 

# Instruction: 
Generate the expected execution output (output from all print() functions) of the code. 
You don't have to actually run the code and do not care about 'not implemented error'.
"""
    assistant_message9 = """\
Starting analysis of the headline: Greyhound Retail Park: Police hunt cyclist after crash | Echo - Echo
Extracted News Source: Echo
Is the headline discussing an accident? Yes, based on rationale: The headline explicitly mentions a 'crash', indicating an accident.
Party behaviors: {'cyclist': 'being hunted by police after crash', 'police': 'hunting cyclist'}
Law analysis: cyclist violated the law. Rationale: The phrase 'police hunt' suggests a violation or fault.
Law analysis: police did not violate the law. Rationale: 'Hunting' indicates enforcement action, not a violation.
Tone analysis: cyclist is described as 'negative', suggesting culpability or wrongdoing.
Tone analysis: police is described as 'neutral', suggesting a role of enforcement without implied fault.
Most likely accident-related fault party: cyclist
Therefore, the fault is attributed to Cyclist.
News Coverage Analysis Result: The Echo tends to report on cycling incidents with a focus on law enforcement and cyclist responsibilities, often highlighting accidents and conflicts without a strong advocacy stance for cycling safety.
Intermediate Rationale: The headline implies a negative perception towards the cyclist by focusing on the police hunt after a crash, suggesting culpability or wrongdoing. Therefore, it's possibly negative perception towards the cyclist.
Final answer:('Yes', 'Cyclist', 'Negative')""" # guilty or criminal
    
    
    user_message10 = """\
```python
input_text =  "Driver pleads guilty to critically injuring cyclist in Avon Lake - Cleveland 19 News"
publisher_title =  "Cleveland 19 News"
bike_frame = BikeFrame(input_text, publisher_title)
final_answer = bike_frame.analyze_headline()
print("Final answer:"+ final_answer)
``` 

# Instruction: 
Generate the expected execution output (output from all print() functions) of the code. 
You don't have to actually run the code and do not care about 'not implemented error'.
"""
    assistant_message10 = """\
Starting analysis of the headline: Driver pleads guilty to critically injuring cyclist in Avon Lake - Cleveland 19 News
Extracted News Source: Cleveland 19 News
Is the headline discussing an accident? Yes, based on rationale: The headline explicitly mentions a driver pleading guilty to critically injuring a cyclist, indicating an accident, collision, injury occurred.
Party behaviors: {'Driver': 'pleads guilty to critically injuring', 'Cyclist': 'critically injured'}
Law analysis: Driver violated the law. Rationale: Pleading guilty to critically injuring a cyclist implies a violation of traffic laws.
Law analysis: Cyclist did not violate the law. Rationale: Being critically injured does not imply a violation of traffic laws.
Tone analysis: Driver is described as 'guilty', suggesting a negative portrayal.
Tone analysis: Cyclist is described as 'victim', suggesting a sympathetic portrayal.
Most likely accident-related fault party: Driver
Therefore, the fault is attributed to Other.
News Coverage Analysis Result: Cleveland 19 News typically covers stories related to cyclists with a focus on road safety and the consequences of traffic violations, often portraying cyclists in a sympathetic light.
Intermediate Rationale: The headline directly attributes the cause of the accident to the driver's behavior, suggesting that the driver is responsible for the incident. The portrayal of the Cyclist as a victim of the accident suggests a positive perception towards the cyclist.
Final answer:(Yes, Other, Positive)""" # guilty for injuring
    
    
    user_message11 = """\
```python
input_text =  "Norfolk lorry driver set for trial Bungay cyclist death - Eastern Daily Press"
publisher_title =  "Eastern Daily Press"
bike_frame = BikeFrame(input_text, publisher_title)
final_answer = bike_frame.analyze_headline()
print("Final answer:"+ final_answer)
``` 

# Instruction: 
Generate the expected execution output (output from all print() functions) of the code. 
You don't have to actually run the code and do not care about 'not implemented error'.
"""
    assistant_message11 = """\
Starting analysis of the headline: Norfolk lorry driver set for trial Bungay cyclist death - Eastern Daily Press
Extracted News Source: Eastern Daily Press
Is the headline discussing an accident? Yes, based on rationale: The headline explicitly mentions a cyclist's death, and the involvement of a lorry driver who is set for trial.
Party behaviors: {'Norfolk lorry driver': 'set for trial', 'Bungay cyclist': 'death'}
Law analysis: Norfolk lorry driver violated the law. Rationale: The phrase 'set for trial' implies legal proceedings due to a violation.
Law analysis: Bungay cyclist did not violate the law. Rationale: The mention of 'death' does not imply fault.
Tone analysis: Norfolk lorry driver is described as 'Negative', suggesting a critical or accusatory portrayal.
Tone analysis: Bungay cyclist is described as 'Positive', suggesting sympathy or a favorable portrayal due to the tragic outcome 'death'.
Most likely accident-related fault party: Norfolk lorry driver
Therefore, the fault is attributed to Other.
News Coverage Analysis Result: The Eastern Daily Press has a history of reporting on cyclist incidents with a focus on road safety and often highlights the challenges faced by cyclists, suggesting a generally neutral to slightly positive tone towards cyclists.
Intermediate Rationale: The headline suggests that the Norfolk lorry driver is facing legal consequences, implying potential fault in the incident. Additionally, the mention of the Bungay cyclist's death evokes sympathy, portraying them as victim. Therefore, it suggests positive perception towards the cyclist.
Final answer:('Yes', 'Other', 'Positive')""" # guilty for injuring
    
    
    user_message12 = """\
```python
input_text =  "Spectator seriously hurt as pro cyclist crashes into crowd - Times of India"
publisher_title =  "Times of India"
bike_frame = BikeFrame(input_text, publisher_title)
final_answer = bike_frame.analyze_headline()
print("Final answer:"+ final_answer)
``` 

# Instruction: 
Generate the expected execution output (output from all print() functions) of the code. 
You don't have to actually run the code and do not care about 'not implemented error'.
"""
    assistant_message12 = """\
Starting analysis of the headline: Spectator seriously hurt as pro cyclist crashes into crowd - Times of India
Extracted News Source: Times of India
Is the headline discussing an accident? Yes, based on rationale: The headline explicitly mentions a pro cyclist crashing into a crowd, resulting in a spectator being seriously hurt, indicating an accident.
Party behaviors: {'Pro cyclist': 'crashes into crowd', 'Spectator': 'seriously hurt'}
Law analysis: Pro cyclist violated the law. Rationale: Crashing into a crowd and causing harm indicates a violation of safety regulations and potentially criminal negligence.
Law analysis: Spectator did not violate the law. Rationale: Being hurt as a result of an accident does not imply a violation of laws on the spectator's part.
Tone analysis: Pro cyclist is described as 'crashes into crowd', suggesting a negative portrayal.
Tone analysis: Spectator is described as 'seriously hurt', suggesting a sympathetic portrayal.
Most likely accident-related fault party: Pro cyclist
Therefore, the fault is attributed to Cyclist.
News Coverage Analysis Result: Times of India typically covers cycling incidents with a focus on safety and legal implications, often highlighting the consequences of accidents involving cyclists and the impact on spectators and the community.
Intermediate Rationale: The headline highlights the negative outcome of a pro cyclist crashing into a crowd, resulting in a spectator being seriously hurt. The portrayal of the pro cyclist's actions as causing harm to others suggests a negative perception towards the cyclist.
Final answer:('Yes', 'Cyclist', 'Negative')""" # negative behavior

    
    user_message13 = """\
```python
input_text =  "Cyclist, 14, killed in East Gwillimbury collision, police say - CityNews Toronto"
publisher_title =  "CityNews Toronto"
bike_frame = BikeFrame(input_text, publisher_title)
final_answer = bike_frame.analyze_headline()
print("Final answer:"+ final_answer)
``` 

# Instruction: 
Generate the expected execution output (output from all print() functions) of the code. 
You don't have to actually run the code and do not care about 'not implemented error'.
"""
    assistant_message13 = """\
Starting analysis of the headline: Cyclist, 14, killed in East Gwillimbury collision, police say - CityNews Toronto
Extracted News Source: CityNews Toronto
Is the headline discussing an accident? Yes, based on rationale: The headline explicitly mentions a collision resulting in the death of a cyclist, indicating a serious accident.
Party behaviors: {'Cyclist, 14': 'killed in East Gwillimbury collision', 'Other party': 'involved in collision'}
Law analysis: Cyclist, 14 did not violate the law. Rationale: There is no information in the headline suggesting the cyclist violated any traffic laws.
Law analysis: Other party did not violate the law. Rationale: Without further details, it cannot be determined if the other party violated any traffic laws.
Tone analysis: Cyclist, 14 is described as 'victim', suggesting sympathetic implications.
Tone analysis: Other party is described as 'involved in collision', suggesting neutral implications.
Most likely accident-related fault party: Unknown
Therefore, the fault is attributed to Unknown.
News Coverage Analysis Result: CityNews Toronto generally approaches its coverage on cyclists with a focus on specific incidents and safety concerns, often highlighting tensions between cyclists and law enforcement or city policies. The tone is investigative and sometimes critical, particularly when addressing issues like police interactions with cyclists and the impact of city infrastructure decisions on cyclist safety. 
Intermediate Rationale: The headline reports on a tragic event involving a young cyclist who was killed in a collision. The focus on the outcome for the cyclist and the use of the term "killed" may evoke a sympathetic response towards the cyclist. Therefore, it implies a positive perception towards cyclist.
Final answer: ('Yes', 'Unknown', 'Positive')""" # injury in collision or crash
    
    
    user_message14 = """\
```python
input_text =  "Cyclist in critical condition after early morning car crash - MyStateline.com"
publisher_title =  "MyStateline.com"
bike_frame = BikeFrame(input_text, publisher_title)
final_answer = bike_frame.analyze_headline()
print("Final answer:"+ final_answer)
``` 

# Instruction: 
Generate the expected execution output (output from all print() functions) of the code. 
You don't have to actually run the code and do not care about 'not implemented error'.
"""
    assistant_message14 = """\
Starting analysis of the headline: Cyclist in critical condition after early morning car crash - MyStateline.com
Extracted News Source: MyStateline.com
Is the headline discussing an accident? Yes, based on rationale: The headline explicitly mentions a 'car crash' involving a cyclist, indicating an accident.
Party behaviors: {'Cyclist': 'in critical condition', 'Car': 'involved in crash'}
Law analysis: Cyclist did not violate the law. Rationale: The headline does not provide details on the cyclist's behavior violating any traffic laws.
Law analysis: Car did not violate the law. Rationale: The headline does not provide details on the car's behavior violating any traffic laws.
Tone analysis: Cyclist is described as 'victim', suggesting the headline portrays the cyclist sympathetically.
Tone analysis: Car is described as 'involved in crash', suggesting neutral implications.
Most likely accident-related fault party: Unknown
Therefore, the fault is attributed to Unknown.
News Coverage Analysis Result: MyStateline.com typically covers cycling incidents with a focus on factual reporting and community impact, often highlighting safety concerns and the consequences of accidents without strong bias.
Intermediate Rationale: The headline emphasizes the critical condition of the cyclist after a car crash, portraying the cyclist as a victim in need of sympathy and support, leading to a positive perception towards the cyclist.
Final answer:('Yes', 'Unknown', 'Positive')""" # injury in collision or crash

###########################################################################################
# special cases: injuries caused by a crash or collision suggest fault is unknown, while being struck or hit implies fault from another party.
###########################################################################################
    
    user_message15 = """\
```python
input_text =  "Bronx cyclist critically injured when struck by car that drove off: NYPD - WPIX 11 New York"
publisher_title =  "WPIX 11 New York"
bike_frame = BikeFrame(input_text, publisher_title)
final_answer = bike_frame.analyze_headline()
print("Final answer:"+ final_answer)
``` 

# Instruction: 
Generate the expected execution output (output from all print() functions) of the code. 
You don't have to actually run the code and do not care about 'not implemented error'.
"""
    assistant_message15 = """\
Starting analysis of the headline: Bronx cyclist critically injured when struck by car that drove off: NYPD - WPIX 11 New York
Extracted News Source: WPIX 11 New York
Is the headline discussing an accident? Yes, based on rationale: The headline explicitly mentions a cyclist being struck by a car and critically injured, which clearly indicates an accident.
Party behaviors:  {'Bronx cyclist': 'struck by car', 'car': 'drove off after striking cyclist'}
Law analysis: Bronx cyclist did not violate the law. Rationale: The headline does not provide information suggesting the cyclist violated any laws.
Law analysis: car violated the law. Rationale: Leaving the scene after striking a cyclist is a violation of traffic laws.
Tone analysis: Bronx cyclist is described as 'critically injured', suggesting sympathetic implications.
Tone analysis: car is described as 'fled the scene', suggesting negative implications.
Most likely accident-related fault party: car
Therefore, the fault is attributed to Other.
News Coverage Analysis Result: WPIX 11 New York tends to cover stories about cyclists with a focus on local community impact, safety, and incidents involving cyclists. The coverage is typically straightforward and aims to inform the community about developments that affect public safety and urban mobility. The tone is generally neutral, emphasizing the facts of each incident or policy affecting cyclists, without apparent bias or sensationalism.
Intermediate Rationale: The headline's passive language, like "struck" and "drove off," paints the cyclist as a victim and suggests fault lies with the driver who fled. The headline focuses on the injury of the cyclist caused by a hit-and-run incident, emphasizing the seriousness of the cyclist's condition and the illegal action of the car driver. This could lead to a perception that sympathizes with the cyclist, implying a positive peception towards the cyclist.
Final answer: ('Yes', 'Other', 'Positive')""" # injury by struck
    
    
    user_message16 = """\
```python
input_text =  "Cyclist struck at Kitchener intersection | TheRecord.com - TheRecord.com"
publisher_title =  "TheRecord.com"
bike_frame = BikeFrame(input_text, publisher_title)
final_answer = bike_frame.analyze_headline()
print("Final answer:"+ final_answer)
``` 

# Instruction: 
Generate the expected execution output (output from all print() functions) of the code. 
You don't have to actually run the code and do not care about 'not implemented error'.
"""
    assistant_message16 = """\
Starting analysis of the headline: Cyclist struck at Kitchener intersection | TheRecord.com - TheRecord.com
Extracted News Source: TheRecord.com
Is the headline discussing an accident? Yes, based on rationale: The headline explicitly mentions a cyclist being struck, which indicates a collision.
Party behaviors: {'Cyclist': 'struck', 'Vehicle': 'striking'}
Law analysis: Cyclist did not violate the law. Rationale: Being struck does not inherently indicate a violation of traffic laws by the cyclist.
Law analysis: Vehicle violated the law. Rationale: Striking a cyclist typically indicates a failure to yield right of way.
Tone analysis: Cyclist is described as 'victim', suggesting a sympathetic portrayal.
Tone analysis: Vehicle is described as 'aggressor', suggesting a negative portrayal.
Most likely accident-related fault party: Vehicle
Therefore, the fault is attributed to Other.
News Coverage Analysis Result: TheRecord.com typically covers cyclist incidents with a focus on factual reporting and safety awareness, often highlighting accidents and their impact on cyclists and road safety.
Intermediate Rationale: The headline portrays the cyclist as a victim of an incident. The news source's history of advocating for cyclist safety further supports a positive or at least neutral portrayal. Overall, it suggesting a sympathetic portrayal that implies a positive perception towards the cyclist.
Final answer:('Yes', 'Other', 'Positive')""" # injury by struck

    
    user_message17 = """\
```python
input_text =  "After being hit by a truck, cyclist giving back to hospital that helped her - FortSaskOnline.com"
publisher_title =  "FortSaskOnline.com"
bike_frame = BikeFrame(input_text, publisher_title)
final_answer = bike_frame.analyze_headline()
print("Final answer:"+ final_answer)
``` 

# Instruction: 
Generate the expected execution output (output from all print() functions) of the code. 
You don't have to actually run the code and do not care about 'not implemented error'.
"""
    assistant_message17 = """\
Starting analysis of the headline: After being hit by a truck, cyclist giving back to hospital that helped her - FortSaskOnline.com
Extracted News Source: FortSaskOnline.com
Is the headline discussing an accident? Yes, based on rationale: The headline explicitly mentions a cyclist being hit by a truck, which indicates an accident.
Party behaviors: {'Cyclist': 'being hit', 'Truck': 'hitting'}
Law analysis: Cyclist did not violate the law. Rationale: The cyclist's behavior of 'being hit' does not imply a violation of traffic laws.
Law analysis: Truck violated the law. Rationale: The truck's behavior of 'hitting' implies a failure to yield right of way or maintain safe following distance.
Tone analysis: Cyclist is described as 'victim', suggesting a sympathetic portrayal.
Tone analysis: Truck is described as 'aggressor', suggesting a negative portrayal.
Most likely accident-related fault party: Truck
Therefore, the fault is attributed to Other.
News Coverage Analysis Result: FortSaskOnline.com typically covers stories related to cyclists with a focus on community impact and positive outcomes, often highlighting resilience and support within the cycling community.
Intermediate Rationale: The headline portrays the cyclist as a victim of a truck collision, emphasizing the hospital's assistance and the cyclist's subsequent act of gratitude. This narrative evokes sympathy for the cyclist and portrays the cyclist positively, suggesting a positive perception towards cyclist.
Final answer:('Yes', 'Other', 'Positive')""" # injure hit by a truck
    
    
    user_message18 = """\
```python
input_text =  "Cyclist injured in Metheringham hit and run - The Lincolnite"
publisher_title =  "The Lincolnite"
bike_frame = BikeFrame(input_text, publisher_title)
final_answer = bike_frame.analyze_headline()
print("Final answer:"+ final_answer)
``` 

# Instruction: 
Generate the expected execution output (output from all print() functions) of the code. 
You don't have to actually run the code and do not care about 'not implemented error'.
"""
    assistant_message18 = """\
Starting analysis of the headline: Cyclist injured in Metheringham hit and run - The Lincolnite
Extracted News Source: The Lincolnite
Is the headline discussing an accident? Yes, based on rationale: The headline explicitly mentions a cyclist being injured in a hit and run, which directly indicates an accident involving a collision.
Party behaviors: {'Cyclist': 'injured', 'Unknown Driver': 'hit and run'}
Law analysis: Cyclist did not violate the law. Rationale: The cyclist was injured, which does not inherently suggest a violation on their part.
Law analysis: Unknown Driver violated the law. Rationale: 'Hit and run' is a clear violation of traffic laws, indicating that the driver left the scene of an accident without reporting or assisting.
Tone analysis: Cyclist is described as 'Victim', suggesting the headline portrays the cyclist sympathetically as an injured party in the accident.
Tone analysis: Unknown Driver is described as 'hit and run', suggesting the headline implies a negative judgment towards the driver's actions.
Most likely accident-related fault party: Unknown Driver
Therefore, the fault is attributed to Other.
News Coverage Analysis Result: The Lincolnite typically covers cyclist incidents with a focus on safety and community impact, often highlighting accidents and legal actions related to cycling incidents.
Intermediate Rationale: The headline directly attributes the cause of the accident to the 'hit and run' by an unknown driver, which evokes sympathy and portrays the cyclist as a victim. This suggests a positive perception towards cyclist.
Final answer:('Yes', 'Other', 'Positive')""" # injury hit and run
    

    # Few-shot prompting    
    messages = [
        {"role": "system", 'content': system_message},
        {"role": "user", "content": user_message1},
        {"role": "assistant", "content": assistant_message1},
        {"role": "user", "content": user_message2},
        {"role": "assistant", "content": assistant_message2},
        {"role": "user", "content": user_message3},
        {"role": "assistant", "content": assistant_message3},
        {"role": "user", "content": user_message4},
        {"role": "assistant", "content": assistant_message4},
        {"role": "user", "content": user_message5},
        {"role": "assistant", "content": assistant_message5},
        {"role": "user", "content": user_message6},
        {"role": "assistant", "content": assistant_message6},
        {"role": "user", "content": user_message7},
        {"role": "assistant", "content": assistant_message7},
        {"role": "user", "content": user_message8},
        {"role": "assistant", "content": assistant_message8},
        {"role": "user", "content": user_message9},
        {"role": "assistant", "content": assistant_message9},
        {"role": "user", "content": user_message10},
        {"role": "assistant", "content": assistant_message10},
        {"role": "user", "content": user_message11},
        {"role": "assistant", "content": assistant_message11},
        {"role": "user", "content": user_message12},
        {"role": "assistant", "content": assistant_message12},
        {"role": "user", "content": user_message13},
        {"role": "assistant", "content": assistant_message13},
        {"role": "user", "content": user_message14},
        {"role": "assistant", "content": assistant_message14},
        {"role": "user", "content": user_message15},
        {"role": "assistant", "content": assistant_message15},
        {"role": "user", "content": user_message16},
        {"role": "assistant", "content": assistant_message16},
        {"role": "user", "content": user_message17},
        {"role": "assistant", "content": assistant_message17},
        {"role": "user", "content": user_message18},
        {"role": "assistant", "content": assistant_message18},
        {"role": "user", "content": user_input},
    ]
    
    return messages