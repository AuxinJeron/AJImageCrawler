import argparse
import asyncio
import base64
import uuid
import urllib
import os
from pyppeteer import launch
from tqdm import tqdm

def retrieve_user_input():
    parser = argparse.ArgumentParser(description="Run image crawler.")
    parser.add_argument("--key-words", type=str, required=True)
    parser.add_argument("--max-results", type=int, required=False)
    parser.add_argument("--output-dir", type=str, required=True)

    return vars(parser.parse_args())

def run_crawler(key_words, output_dir):
    NotImplemented()

def generate_id():
    return base64.urlsafe_b64encode(uuid.uuid4().bytes).decode("utf-8")[:-2]

# main program
async def main():
    args = retrieve_user_input()
    print("Got the arguments")
    print(args)

    key_words = args["key_words"]
    max_results = args.get("max_results")
    if max_results == None:
        max_results = float("inf")
    output_dir = args["output_dir"]

    print("Collecting images ...")
    browser = await launch({"headless": True})
    # Create new incognito browser context
    context = await browser.createIncognitoBrowserContext()
    # Create a new page inside context
    page = await context.newPage()
    await page.goto(f"https://www.google.com/search?q={key_words}&tbm=isch")
    await page.setViewport({
        "width": 1200,
        "height": 800
    })
    images = []
    more_btn = None
    while len(images) < max_results:
        load_images = await page.evaluate(
            '''
            () => {
                let results = [];
                let items = document.querySelectorAll("div[jsaction] > img");
                items.forEach(item => {
                    if (item.getAttribute("src") != null) {
                        results.push(item.getAttribute("src"))
                    }
                });
                return results;
            }
            '''
        )

        previous_height = await page.evaluate("document.body.scrollHeight")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.waitForFunction(f"document.body.scrollHeight >= {previous_height}")
        await page.waitFor(1000)

        # There is no more images
        if len(images) == len(load_images):
            if more_btn is None:
                more_btn = await page.waitForSelector("input[value='Show more results']", {"visible": True, "timeout": 1000})
                await more_btn.click()
                await page.waitFor(1000)
            else:
                break
        images = load_images
    await browser.close()

    images_size = min(max_results, len(images))
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    for i in tqdm(range(0, images_size)):
        try:
            file_path = os.path.join(output_dir, f"{generate_id()}.jpg")
            urllib.request.urlretrieve(images[i], file_path)
        except Exception as e:
            print(e)

    print(f"There are {images_size} downloaded.")

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
