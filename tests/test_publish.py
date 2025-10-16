import responses

from fiboa_cli.publish import Publish


class TestPublish(Publish):
    def generate_pmtiles(self, target, file_name, parquet_file):
        pass

    def upload_to_aws(self, target):
        pass


@responses.activate
def test_publish(tmp_folder):
    converter = "be_vlg"
    base = "BE-VLG"
    path = f"tests/data-files/convert/{converter}"
    rsp1 = responses.Response(
        method="GET",
        url=f"https://raw.githubusercontent.com/fiboa/data-survey/refs/heads/main/data/{base}.md",
        body=open(f"tests/data-files/publish/{base}-survey.md").read(),
    )
    responses.add(rsp1)
    TestPublish(converter).run(
        variant="2023", target=tmp_folder, cache=path, generate_meta=True, yes=True
    )
    files = [f.name for f in tmp_folder.iterdir() if f.is_file()]
    for f in ("README.md", "LICENSE.txt", "be_vlg-2023.parquet"):
        assert f in files, f"Missing file {f}"
