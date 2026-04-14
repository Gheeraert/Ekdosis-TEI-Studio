from __future__ import annotations

from .models import (
    Annotation,
    AnnotationCollection,
    AnnotationDiagnostic,
    AnnotationValidationError,
)


def create_annotation(collection: AnnotationCollection, annotation: Annotation) -> AnnotationCollection:
    if any(existing.id == annotation.id for existing in collection.annotations):
        raise AnnotationValidationError(
            [AnnotationDiagnostic(code="E_ANN_DUPLICATE_ID", message=f"Duplicate annotation id: {annotation.id}.", annotation_id=annotation.id)]
        )
    return AnnotationCollection(version=collection.version, annotations=[*collection.annotations, annotation])


def update_annotation(collection: AnnotationCollection, annotation: Annotation) -> AnnotationCollection:
    updated = False
    annotations: list[Annotation] = []
    for existing in collection.annotations:
        if existing.id == annotation.id:
            annotations.append(annotation)
            updated = True
        else:
            annotations.append(existing)
    if not updated:
        raise AnnotationValidationError(
            [
                AnnotationDiagnostic(
                    code="E_ANN_NOT_FOUND",
                    message=f"Cannot update missing annotation id: {annotation.id}.",
                    annotation_id=annotation.id,
                )
            ]
        )
    return AnnotationCollection(version=collection.version, annotations=annotations)


def delete_annotation(collection: AnnotationCollection, annotation_id: str) -> AnnotationCollection:
    remaining = [annotation for annotation in collection.annotations if annotation.id != annotation_id]
    if len(remaining) == len(collection.annotations):
        raise AnnotationValidationError(
            [
                AnnotationDiagnostic(
                    code="E_ANN_NOT_FOUND",
                    message=f"Cannot delete missing annotation id: {annotation_id}.",
                    annotation_id=annotation_id,
                )
            ]
        )
    return AnnotationCollection(version=collection.version, annotations=remaining)
