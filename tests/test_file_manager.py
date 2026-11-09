import pytest

from automation import file_manager as fm


@pytest.fixture(autouse=True)
def fake_folders(tmp_path, monkeypatch):
    """Use temporary folders instead of your real Desktop and Documents."""
    roots = {}
    for name in ("desktop", "documents", "downloads"):
        folder = tmp_path / name
        folder.mkdir()
        roots[name] = folder.resolve()
    monkeypatch.setattr(fm, "APPROVED_ROOTS", roots)
    return roots


def test_create_folder(fake_folders):
    result = fm.create_folder("Python Learning", "desktop")
    assert "Created folder" in result
    assert (fake_folders["desktop"] / "Python Learning").is_dir()


def test_create_folder_twice_does_not_overwrite(fake_folders):
    fm.create_folder("Notes", "desktop")
    assert "already exists" in fm.create_folder("Notes", "desktop")


@pytest.mark.parametrize("bad", ["..", "a/b", "a\\b", "x:y", "", "   ", "what?"])
def test_bad_folder_names_are_refused(bad):
    assert "not allowed" in fm.create_folder(bad, "desktop")


def test_outside_folder_is_refused(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    assert "only allowed" in fm.list_folder(str(outside))
    assert "only allowed" in fm.create_folder("x", str(outside))


def test_list_folder(fake_folders):
    (fake_folders["desktop"] / "Photos").mkdir()
    (fake_folders["desktop"] / "a.txt").write_text("hi")
    result = fm.list_folder("desktop")
    assert "1 folders and 1 files" in result
    assert "Photos" in result and "a.txt" in result


def test_search_files(fake_folders):
    (fake_folders["documents"] / "Resume_2026.docx").write_text("x")
    assert "Resume_2026.docx" in fm.search_files("resume", "documents")
    assert "found nothing" in fm.search_files("zzz", "documents")


def test_rename_needs_confirmation(fake_folders):
    (fake_folders["desktop"] / "Old").mkdir()
    result = fm.rename_item("Old", "New", "desktop")
    assert "confirm" in result
    assert (fake_folders["desktop"] / "Old").exists()      # nothing changed
    assert not (fake_folders["desktop"] / "New").exists()


def test_rename_confirmed(fake_folders):
    (fake_folders["desktop"] / "Old").mkdir()
    assert "Renamed" in fm.rename_item("Old", "New", "desktop", confirmed=True)
    assert (fake_folders["desktop"] / "New").exists()
    assert not (fake_folders["desktop"] / "Old").exists()


def test_rename_never_overwrites(fake_folders):
    (fake_folders["desktop"] / "A").mkdir()
    (fake_folders["desktop"] / "B").mkdir()
    assert "already exists" in fm.rename_item("A", "B", "desktop", confirmed=True)
    assert (fake_folders["desktop"] / "A").exists()


def test_rename_missing_item(fake_folders):
    assert "could not find" in fm.rename_item("Nope", "X", "desktop", confirmed=True)


def test_move_needs_confirmation_then_works(fake_folders):
    (fake_folders["desktop"] / "Stuff").mkdir()
    assert "confirm" in fm.move_item("Stuff", "documents")
    assert (fake_folders["desktop"] / "Stuff").exists()
    assert "Moved" in fm.move_item("Stuff", "documents", confirmed=True)
    assert (fake_folders["documents"] / "Stuff").exists()
    assert not (fake_folders["desktop"] / "Stuff").exists()


def test_move_never_overwrites(fake_folders):
    (fake_folders["desktop"] / "Same").mkdir()
    (fake_folders["documents"] / "Same").mkdir()
    assert "already exists" in fm.move_item("Same", "documents", confirmed=True)


def test_cannot_move_folder_into_itself(fake_folders):
    parent = fake_folders["desktop"] / "Parent"
    (parent / "Child").mkdir(parents=True)
    result = fm.move_item("Parent", str(parent / "Child"), "desktop", confirmed=True)
    assert "into itself" in result
