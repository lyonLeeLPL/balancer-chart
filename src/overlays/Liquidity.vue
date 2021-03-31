<script>
  // Standalone renedrer for the volume

  import Overlay from 'trading-vue-js/src/mixins/overlay.js'
  // import Candle from '../primitives/candle.js'

  export default {
    name: 'Liquidity',
    mixins: [Overlay],
    methods: {
      meta_info() {
        return { author: 'OnlyC', version: '1.1.0' }
      },

      // Here goes your code. You are provided with:
      // { All stuff is reactive }
      // $props.layout -> positions of all chart elements +
      //  some helper functions (see layout_fn.js)
      // $props.interval -> candlestick time interval
      // $props.sub -> current subset of candlestick data
      // $props.data -> your indicator's data subset.
      //  Comes "as is", should have the following format:
      //  [[<timestamp>, ... ], ... ]
      // $props.colors -> colors (see TradingVue.vue)
      // $props.cursor -> current position of crosshair
      // $props.settings -> indicator's custom settings
      //  E.g. colors, line thickness, etc. You define it.
      // $props.num -> indicator's layer number (of All
      // layers in the current grid)
      // $props.id -> indicator's id (e.g. EMA_0)
      // ~
      // Finally, let's make the canvas dirty!
      draw(ctx) {
        ctx.lineWidth = this.line_width
        ctx.strokeStyle = this.color
        ctx.beginPath()

        const layout = this.$props.layout
        const i = 1
        const data = this.$props.data

        if (!this.skip_nan) {
          for (let k = 0, n = data.length; k < n; k++) {
            const p = data[k]
            const x = layout.t2screen(p[0])
            const y = layout.$2screen(p[i])
            ctx.lineTo(x, y)
          }
        } else {
          let skip = false
          for (let k = 0, n = data.length; k < n; k++) {
            const p = data[k]
            const x = layout.t2screen(p[0])
            const y = layout.$2screen(p[i])
            if (p[i] == null || y !== y) {
              skip = true
            } else {
              if (skip) ctx.moveTo(x, y)
              ctx.lineTo(x, y)
              skip = false
            }
          }
        }
        ctx.stroke()
      },
      use_for() {
        return ['Liquidity']
      },
      data_colors() {
        return [this.color]
      },
      legend(values) {
        return [{ value: this.MoneyFormat(values[1]) }, { color: this.color }]
      },
      MoneyFormat(labelValue) {
        // Nine Zeroes for Billions
        return Math.abs(Number(labelValue)) >= 1.0e9
          ? `${(Math.abs(Number(labelValue)) / 1.0e9).toFixed(2)}B`
          : // Six Zeroes for Millions
          Math.abs(Number(labelValue)) >= 1.0e6
          ? `${(Math.abs(Number(labelValue)) / 1.0e6).toFixed(2)}M`
          : // Three Zeroes for Thousands
          Math.abs(Number(labelValue)) >= 1.0e3
          ? `${(Math.abs(Number(labelValue)) / 1.0e3).toFixed(2)}K`
          : Math.abs(Number(labelValue)).toFixed(2)
      }
    },

    // Define internal setting & constants here
    computed: {
      sett() {
        return this.$props.settings
      },
      line_width() {
        return this.sett.lineWidth || 0.75
      },
      color() {
        const n = this.$props.num % 5
        return this.sett.color || this.COLORS[n]
      },
      data_index() {
        return this.sett.dataIndex || 1
      },
      // Don't connect separate parts if true
      skip_nan() {
        return this.sett.skipNaN
      }
    },
    data() {
      return {
        COLORS: ['#42b28a', '#5691ce', '#612ff9', '#d50b90', '#ff2316']
      }
    }
  }
</script>
