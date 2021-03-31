export default {
  copy(obj, mod) {
    const copy = JSON.parse(JSON.stringify(obj))
    return Object.assign(copy, mod)
  },

  removed(ids, prev) {
    const list = []
    for (const id of prev) {
      if (!ids.includes(id)) {
        list.push(id)
      }
    }
    return list
  }
}
