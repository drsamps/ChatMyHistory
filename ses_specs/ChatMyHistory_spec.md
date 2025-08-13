I want an app that interviews an elderly person to create a rich, usable life history, you’ll want to design it with **three overlapping priorities**:

* **Ease of use for seniors** (clear, simple, and accessible UI)
* **Richness and structure of captured content** (photos, audio, video, text)
* **Long-term organization and sharing** (archive, export, privacy)

I would like to implement it to run on a Ubuntu Linux server running the Apache2 web server.  Backend techologies include:
* written in Python
* utilize a mysql database with credentials specified in an .env file (provide an .env-example file)
* call LLMs from OpenAI/Google/Anthropic
* be implemented using Flask
* utilize the Web Server Gateway Interface (WSGI).
The frontend should be written in HTML/JavaScript/CSS to display an Chrome or other common web browser, including running on a mobile device.
Admin users can control options and features such as:
* Create/edit/delete other users
* Control LLM access
* Make adjustment to LLM system prompts
Regular users have easy access to various features.  The biggest feature is having the person voice or text chat with an AI who interviews them to record and organize their personal history.  The output is an organized data file of their personal history to share and enjoy.

Here’s a **feature breakdown** that the app might include:
(as recommended by https://chatgpt.com/c/68994875-8800-8327-8838-399a21ee8acd)

---

## **1. User Experience & Accessibility**

* **Large, high-contrast text and buttons** for easy navigation.
* **Voice interaction** so the user can speak instead of tapping menus.
* **Simple step-by-step flow** (avoid overwhelming menus).
* **Adjustable font size & color contrast** for vision needs.
* **Multi-language support** if relevant to their background.
* **Offline mode** in case of low internet access.

---

## **2. Guided Interview Structure**

* **Thematic Question Sets** (e.g., Childhood, Family, Career, Historical Events, Life Lessons).
* **Adaptive Questioning**: The app adjusts follow-up questions based on previous answers.
* **Icebreaker prompts** to make the person comfortable.
* **Timeline mode** to capture events chronologically.
* **Custom questions** that family members can add before the interview.

---

## **3. Recording & Media Capture**

* **Audio recording** (primary for ease of use and emotional nuance).
* **Optional video recording** for facial expressions and body language.
* **Photo prompts**: Let the interviewer show old photos and record reactions.
* **Ability to scan or photograph documents** (letters, certificates, newspaper clippings).
* **Background noise reduction** for clearer recordings.

---

## **4. Memory Stimulation Tools**

* **Image prompts** from historical archives (“Here’s a picture of your hometown in the 1950s”).
* **Music prompts** (play songs from the era they grew up in).
* **Location prompts** (map view of places they lived).
* **News event prompts** (“Do you remember where you were when the moon landing happened?”).

---

## **5. Organization & Storybuilding**

* **Automatic transcription** of audio/video recordings.
* **Tagging by topic** (e.g., “war stories,” “parenting,” “travel”).
* **Automatic timeline creation** from stories and events.
* **Chapter generation** for life story formatting.
* **Photo + story pairing** in a scrapbook layout.

---

## **6. Editing & Sharing**

* **Family collaboration**: Allow relatives to add questions, photos, or comments.
* **Automatic summarization** of each session into a readable paragraph.
* **Export formats**: PDF, printed book, slideshow, website.
* **Voice-over playback** of transcribed text in the interviewee’s voice (using voice cloning).

---

## **7. Privacy & Preservation**

* **Clear ownership controls**: Who can access the recordings?
* **Cloud backup** with encryption for safety.
* **Option for local storage only** if privacy is a priority.
* **Integration with digital legacy services** (e.g., archive with libraries or genealogy platforms).

---

## **8. Extra Engagement Features**

* **"Story of the Day" reminders** to prompt short daily recordings.
* **Milestone badges** (“We’ve reached 10 stories!”).
* **Generational sharing**: Let grandchildren record their own reactions or questions.
* **Legacy messages**: Interviewee can record private messages for future delivery.

---
