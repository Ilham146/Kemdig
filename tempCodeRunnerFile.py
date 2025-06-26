@app.route("/delete-permanent/<int:id>")
def delete_permanent(id):
    note = Note.query.get_or_404(id)
    if note.is_deleted:
        db.session.delete(note)
        db.session.commit()
        flash("Catatan berhasil dihapus secara permanen.")
    else:
        flash("Catatan belum dipindahkan ke Recently Deleted.")
    return redirect("/recently-deleted")