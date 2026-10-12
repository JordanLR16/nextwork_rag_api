from importer import InstagramImporter


def test_can_handle_instagram_post_and_reel_urls():
    importer = InstagramImporter()

    assert importer.can_handle("https://www.instagram.com/p/ABC123/")
    assert importer.can_handle("https://instagram.com/reel/XYZ789/?igsh=abc")
    assert not importer.can_handle("https://example.com/p/ABC123/")
    assert not importer.can_handle("https://www.instagram.com/stories/example/1/")


def test_import_media_extracts_metadata_and_caption_recipe():
    importer = InstagramImporter()
    html = """
    <html>
      <head>
        <meta property="og:title" content="@chefcasey on Instagram: Weeknight pasta" />
        <meta property="og:description" content="Tomato Pasta
Ingredients:
- 8 oz pasta
- 1 cup tomato sauce
Instructions:
1. Boil the pasta.
2. Stir in sauce and serve.
#dinner #pasta" />
        <meta property="og:image" content="https://cdn.example.test/thumb.jpg" />
      </head>
    </html>
    """

    content = importer.import_media("https://www.instagram.com/p/ABC123/", html=html)

    assert content.platform == "instagram"
    assert content.external_id == "ABC123"
    assert content.author_name == "@chefcasey"
    assert content.thumbnail_url == "https://cdn.example.test/thumb.jpg"
    assert content.recipe is not None
    assert content.recipe.title == "Tomato Pasta"
    assert content.recipe.ingredients == ["8 oz pasta", "1 cup tomato sauce"]
    assert "Boil the pasta." in content.recipe.instructions
    assert content.recipe.tags == ["dinner", "pasta"]
    assert content.status == "recipe_imported"


def test_import_media_uses_transcript_when_caption_has_no_recipe():
    importer = InstagramImporter()
    html = """
    <html>
      <head>
        <meta property="og:title" content="@chefcasey on Instagram" />
        <meta property="og:description" content="This soup is cozy and fast." />
        <meta property="og:video" content="https://cdn.example.test/video.mp4" />
      </head>
    </html>
    """
    transcript = """
    Lentil Soup
    Ingredients:
    - 1 cup lentils
    - 4 cups broth
    Directions:
    1. Combine lentils and broth in a pot.
    2. Simmer until tender.
    """

    content = importer.import_media("https://www.instagram.com/reel/XYZ789/", transcript=transcript, html=html)

    assert content.media_type == "video"
    assert content.recipe is not None
    assert content.recipe.title == "Lentil Soup"
    assert content.recipe.ingredients == ["1 cup lentils", "4 cups broth"]
    assert "Simmer until tender." in content.recipe.instructions
