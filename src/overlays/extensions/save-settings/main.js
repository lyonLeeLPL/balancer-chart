// Extension's controller

import Shared from './shared.js'
import Utils from './utils.js'

export default class Main {
  constructor(tv, dc, sett) {
    // if (sett.use_window) {
    //   if (!window.xchartlink$) {
    //     window.xchartlink$ = {}
    //   }
    //   this.shared = window.xchartlink$
    // } else {
    //   this.shared = Shared
    // }

    this.tv = tv
    this.dc = dc
    this.sett = sett
    this.targets = {}

    this.onsettings({ 'save-settings': sett })
  }

  // Listens to all tvjs events, creates new widgets
  update(e) {
    switch (e.event) {
      case 'update':
        console.log(e)
    }
  }

  // Extension settings has changed
  onsettings(sett) {
    console.log(sett)
  }

  remove_widget(id) {
    // ...
  }

  destroy() {
    // this.tv.$el.removeEventListener('mousemove', this.onmousemove)
    // this.tv.$el.removeEventListener('mouseup', this.mouseup)
    // this.tv.$el.removeEventListener('mouseleave', this.mouseleave)
  }
}
