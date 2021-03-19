<template>
  <trading-vue
    :data="chart"
    :width="this.width"
    :height="this.height"
    ref="tvjs"
    :title-txt="this.selected"
    :toolbar="true"
    :color-back="colors.colorBack"
    :color-grid="colors.colorGrid"
    :color-text="colors.colorText"
    :overlays="overlays"
  >
  </trading-vue>
</template>

<script>
  import { TradingVue, DataCube } from 'trading-vue-js'
  import Liquidity from '../overlays/Liquidity'

  export default {
    components: { TradingVue },
    data() {
      return {
        chart: new DataCube({
          chart: {},
          onchart: [],
          offchart: [
            {
              name: 'Liquidity',
              type: 'Liquidity',
              data: [],
              settings: {
                'z-index': 10
              }
            }
          ]
        }),
        overlays: [],
        width: window.innerWidth,
        height: window.innerHeight,
        night: true,
        selected: undefined,
        loading: false
      }
    },
    methods: {
      onResize(event) {
        this.width = window.innerWidth
        this.height = window.innerHeight - 50
      },
      async changeSymbol(symbol) {
        if (!symbol || symbol === null) return

        this.loading = true
        const chartData = await this.$http.get(`/bars/${symbol}`)
        // console.log(chartData)
        this.chart.set('chart.data', chartData.data.bars)
        // this.chart.set('offchart.Liquidity.data', chartData.data.liquidity)
        this.selected = symbol

        // this.onResize()
        this.$refs.tvjs.resetChart()
        this.loading = false
      }
    },
    computed: {
      colors() {
        return this.night
          ? {}
          : {
              colorBack: '#fff',
              colorGrid: '#eee',
              colorText: '#333'
            }
      }
    },
    mounted() {
      window.addEventListener('resize', this.onResize)
      this.onResize()
      window.dc = this.chart
      window.tv = this.$refs.tvjs
      this.changeSymbol('BAL-WETH')
    },
    beforeDestroy() {
      window.removeEventListener('resize', this.onResize)
    }
  }
</script>
