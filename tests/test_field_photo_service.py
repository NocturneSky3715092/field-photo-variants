from field_photo_service import WorkOrderPhoto, crop_variants


class FakeClient:
    def crop(self, image, aspect):
        return {"image": f"cropped-{aspect}"}

    def presign_get(self, bucket, key):
        return {"url": f"https://objects.test/{bucket}/{key}"}


def test_dispatch_photo_gets_all_required_views():
    photo = WorkOrderPhoto("WO-7", "encoded", "assigned", "check seal")
    links = crop_variants(photo, FakeClient(), "field-media")
    assert set(links) == {"1:1", "4:3", "16:9"}
    assert links["16:9"].endswith("16-9.jpg")
