# Image Builder - Screen Recording Script

How to use this script:
- Each segment below is separated by `---`.
- **SCREEN** tells you what to open, scroll to or highlight while the narration plays.
- **SAY** is the text for the text-to-speech voice. Copy only the text under **SAY**.
- Open `code-explainer.md` in Markdown preview (Ctrl + Shift + V) so the diagrams are drawn.
  Mermaid diagrams need the *Markdown Preview Mermaid Support* extension.
- Estimated total length: about 10 minutes (21 segments, about 1,570 spoken words).

---

**SCREEN:** `code-explainer.md` preview, scrolled to the top. The title "Image Builder - Code Explainer" is visible.

**SAY:**
Welcome. In this video we will walk through the Image Builder. It is a small Python program that creates an image using generative A I. You describe the picture in a simple text file, and the program asks an A I model in the cloud to draw it for you. Let's see how it works, which files are involved, and how the code runs from start to finish.

---

**SCREEN:** `code-explainer.md` preview, section **1. Objective**. Point the mouse at the four boxes of the first diagram, left to right.

**SAY:**
Here is the whole idea in one picture. First, you describe the image in a prompt file. Second, the image builder script reads that description and checks it. Third, it sends the description to the FLUX one dev image model, which runs on NVIDIA's cloud. And fourth, the finished picture comes back and is saved as a J P G file in the output folder. To make a different image, you never change the code. You only change the prompt file.

---

**SCREEN:** `code-explainer.md` preview, section **2. Files involved**, the table.

**SAY:**
Only a few files are involved. The prompt file is your input, where you write the image type, size and description. The settings dot config file, in the main project folder, holds your secret NVIDIA A P I key. The image builder dot p y file is the whole program. The NVIDIA cloud service is the A I model that draws the picture. And the output folder is where every generated image is saved, with the date and time in its name.

---

**SCREEN:** `code-explainer.md` preview, **Architecture** diagram. Move the mouse from the repository box, to the image-builder box, to the NVIDIA cloud box.

**SAY:**
This architecture diagram shows where each piece lives. On the left is our project folder, with the settings file and the image builder folder inside it. On the right is the NVIDIA cloud. The script sits in the middle. It takes the A P I key from the settings file and the description from the prompt file. It sends a secure web request to the FLUX model, and the model replies with the image. Finally, the script writes that image into the output folder.

---

**SCREEN:** `code-explainer.md` preview, section **3. Data flow diagram**. Point at the legend text first, then at the three cylinders.

**SAY:**
Now let's follow the data itself. This is a data flow diagram. The rectangles are things outside the program: you, the user, and the NVIDIA cloud. The cylinders are the data stores, which are the settings file, the prompt file and the output folder. The rounded boxes are the steps inside the program, and each one is a Python function. The labels on the arrows tell you exactly what data moves between them.

---

**SCREEN:** Same diagram. Trace the arrows with the mouse: settings.config to step 1, image_prompt.txt to step 2, step 2 to steps 3 and 4, then everything into step 5, then step 6 into the output folder.

**SAY:**
Step one reads the A P I key from the settings file. Step two reads the prompt file and splits it into the image type, size and description. The size goes to step three, which turns text like thirteen forty four by seven sixty eight into two numbers. The type and description go to step four, which joins them into one prompt sentence. Step five collects the key, the size and the prompt, and sends them to NVIDIA. The image comes back, and step six saves it to the output folder and prints where it was saved.

---

**SCREEN:** Open `image-builder/image_prompt.txt` in the editor.

**SAY:**
Let's look at the real files, starting with the prompt file. Lines that start with a hash sign are comments, and the program ignores them. Then there are three fields. Image Type is the style, here an anime image. Image Size is the width and height. Image Description is what you want to see, here people in a fair. The description can continue over several lines if you need more detail.

---

**SCREEN:** Open `settings.config` in the editor. **Hide or blur the key values before recording**, or show only the key names.

**SAY:**
The A P I key lives in the settings dot config file in the main project folder. The line starts with N V D I A underscore A P I underscore KEY, followed by an equals sign and your key. You can get a free key from build dot nvidia dot com. Keep this file private, and never share your key. That is why this file is listed in dot git ignore, so it is never uploaded to Git.

---

**SCREEN:** Open `image-builder/image_builder.py`. Show lines 1 to 40: the description at the top, the imports and the constants.

**SAY:**
Now the program itself. At the top is a short description and the usage examples. The imports are all from Python's standard library, so there is nothing extra to install. Below them are the constants. They define where the settings file, the prompt file and the output folder are, the web address of the FLUX model, and the allowed image sizes, which are from seven sixty eight to thirteen forty four pixels, in steps of sixty four.

---

**SCREEN:** `image_builder.py`, highlight the function `load_config` (lines 43 to 52).

**SAY:**
The first function is load config. It opens the settings file and reads it line by line. It skips empty lines and comments. For every line that has an equals sign, it splits the line into a name and a value, removes any quotes around the value, and stores it in a dictionary. That is how the program finds the NVIDIA key.

---

**SCREEN:** `image_builder.py`, highlight `read_prompt_file` (lines 55 to 72). Then switch to the `code-explainer.md` preview and show the flowchart under "How the prompt file is read".

**SAY:**
Next is read prompt file. It reads the prompt file one line at a time and skips comments. When a line starts with one of the three known names, such as Image Type, a new field begins. When a line has no known name, it is added to the field before it. That is what allows a description to span several lines. At the end, the function checks that all three fields are filled. If one is missing, the program stops with a clear message telling you which field is missing.

---

**SCREEN:** `image_builder.py`, highlight `parse_size` (lines 75 to 89). Then show the size table in the `code-explainer.md` preview.

**SAY:**
The parse size function turns the size text into two numbers. First it checks the format, a width, the letter x, and a height. Then it snaps each number to a size the model accepts. It rounds to the nearest multiple of sixty four and keeps the value between seven sixty eight and thirteen forty four. For example, nineteen twenty by ten eighty becomes thirteen forty four by ten eighty eight. If the size was changed, the program prints a short note, so there are no surprises.

---

**SCREEN:** `image_builder.py`, highlight `build_prompt` (lines 92 to 93), then `generate_image` (lines 96 to 116).

**SAY:**
Build prompt simply joins the image type and the description into one sentence, like anime image, people in a fair. Then generate image does the A I work. It packs the prompt, width, height, number of steps and seed into a J SON request, adds the A P I key, and sends it to NVIDIA. The reply contains the picture encoded as base sixty four text. The function checks that the generation succeeded, and then decodes the text back into real image bytes.

---

**SCREEN:** `image_builder.py`, highlight `main` (lines 119 to 145).

**SAY:**
The main function connects everything. It reads the command line options: which prompt file to use, the number of steps, and the seed. It loads the key and stops if the key is missing. It reads the prompt file, fixes the size and builds the prompt. It prints what it is about to do and calls generate image. Finally, it creates the output folder if needed and saves the image, using the prompt file name plus the date and time as the file name.

---

**SCREEN:** `code-explainer.md` preview, section **6. Code execution flow**, the large flowchart. Move down the main path, then point at the red exit boxes.

**SAY:**
This flowchart shows the complete execution path. The main path runs straight down the middle, from reading the options to saving the image. Each diamond is a check, and each red box is a place where the program stops safely with a helpful message. It can stop when the key is missing, when a prompt field is missing, when the size is written wrongly, when the web request fails, or when the model refuses the prompt, for example because of the safety filter.

---

**SCREEN:** `code-explainer.md` preview, the **sequence diagram** below the flowchart.

**SAY:**
Here is the same run as a conversation between the parts. You start the script. The script asks the settings file for the key, and the prompt file for the description. It prepares the size and the prompt, then sends a request to NVIDIA. The model spends a few seconds drawing the image and sends it back. The script decodes it, saves the file in the output folder, and tells you where it is.

---

**SCREEN:** Open the VS Code terminal (Ctrl + backtick). Type and run:
`cd image-builder` then `python image_builder.py`.
Let the output print completely.

**SAY:**
Let's run it. In the terminal, go into the image builder folder and run python image builder dot p y. The program prints the prompt file it used, the image type, the final size and the full prompt. Then it says generating image. After a few seconds it prints saved, followed by the path of the new image.

---

**SCREEN:** In the Explorer, expand `image-builder/output/` and click the newest `.jpg` so it opens in the editor.

**SAY:**
And here is the result, straight from the output folder. This picture was drawn by the A I from one short line of text. Every run creates a new file with its own date and time, so earlier images are never overwritten.

---

**SCREEN:** Terminal. Run `python image_builder.py --seed 42`, then show the new image. Optionally edit the description in `image_prompt.txt` and run again.

**SAY:**
There are two useful options. The seed option makes results repeatable. With the same seed and the same prompt, you get the same image again, while a seed of zero gives a new random image every time. The steps option controls detail. More steps give a more detailed image, but take longer. And to create something completely different, just edit the description in the prompt file and run the script again.

---

**SCREEN:** `code-explainer.md` preview, section **7. Errors you may see**.

**SAY:**
If something goes wrong, check this table. It lists every error message, what causes it, and how to fix it. The most common one is a missing or misspelled key in the settings file. Remember that the name is spelled N V D I A. Also note that the size adjusted message is not an error. It only tells you the size was rounded to a supported value.

---

**SCREEN:** Scroll `code-explainer.md` preview back to the top diagram (section 1).

**SAY:**
To recap. You describe the image in a text file. The script reads and checks it, sends it to the FLUX model on NVIDIA's cloud, and saves the picture in the output folder. It is about one hundred and fifty lines of plain Python, with no extra libraries. Try your own descriptions, and thanks for watching.
