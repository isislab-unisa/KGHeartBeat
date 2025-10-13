import query
import utils

class Accessibility4VisuallyImpaired:
    def __init__(self):
        pass

    def alt_image(self,sparql_endpoint):
        if not utils.is_url(sparql_endpoint):
            return (0, "No SPARQL endpoint provided")
        else:
            images = query.getImageIri(sparql_endpoint)
            if isinstance(images, list) and len(images) > 0:
                count_with_alt = 0
                for i, img in enumerate(images, 1):
                    if query.hasAltDescription(sparql_endpoint, img):
                        count_with_alt += 1
                    if i % 50 == 0:
                        print(f"Processed {i}/{len(images)} images...")
                return (count_with_alt / len(images), len(images))
            if isinstance(images, list) and len(images) == 0:
                return (0, "No images found in the KG")